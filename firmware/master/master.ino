/**
 * ESP8266 Racing Controller - Master Firmware
 * Board: NodeMCU 1.0 (ESP-12E Module)
 */

#include <SoftwareSerial.h>

#define PIN_ENC_CLK       14 // D5 (GPIO14)
#define PIN_ENC_DT        12 // D6 (GPIO12)
#define PIN_ENC_SW        13 // D7 (GPIO13)
#define PIN_JOY_X         A0 // ADC0
#define PIN_RX            4  // D2 (GPIO4)
#define PIN_TX            5  // D1 (GPIO5)

const uint32_t PC_BAUD_RATE         = 115200;
const uint32_t SLAVE_BAUD_RATE      = 19200;
const uint32_t PC_UPDATE_FREQ_HZ    = 100;
const uint32_t UPDATE_INTERVAL_MS   = 1000 / PC_UPDATE_FREQ_HZ;
const uint32_t SLAVE_TIMEOUT_MS     = 100;
const uint32_t DEBOUNCE_DELAY_MS    = 30;

const int8_t   ENCODER_DIR          = 1; 
const uint16_t ADC_EMA_ALPHA        = 64; 
const int16_t  JOY_Y_NEUTRAL        = 512;

volatile int32_t encoderCount = 0;
volatile uint8_t lastClkState = HIGH;

uint8_t  buttonState = 0;
uint8_t  lastButtonRead = HIGH;
uint32_t lastDebounceTime = 0;
uint16_t joyXFiltered = 512;

SoftwareSerial slaveSerial(PIN_RX, PIN_TX);
char     rxBuffer[64];
uint8_t  rxIndex = 0;
uint32_t lastSlaveTime = 0;
int16_t  slaveJoyY = JOY_Y_NEUTRAL;
uint8_t  slaveAccel = 0;
uint8_t  slaveBrake = 0;
uint8_t  slaveClutch = 0;

uint32_t pcSequenceNumber = 0;
uint32_t lastPcUpdate = 0;

void ICACHE_RAM_ATTR encoderISR() {
    uint8_t clk = digitalRead(PIN_ENC_CLK);
    uint8_t dt = digitalRead(PIN_ENC_DT);
    if (clk != lastClkState) {
        lastClkState = clk;
        if (clk == dt) {
            encoderCount += ENCODER_DIR;
        } else {
            encoderCount -= ENCODER_DIR;
        }
    }
}

void setup() {
    Serial.begin(PC_BAUD_RATE);
    slaveSerial.begin(SLAVE_BAUD_RATE);

    pinMode(PIN_ENC_CLK, INPUT_PULLUP);
    pinMode(PIN_ENC_DT, INPUT_PULLUP);
    pinMode(PIN_ENC_SW, INPUT_PULLUP);
    
    lastClkState = digitalRead(PIN_ENC_CLK);
    joyXFiltered = analogRead(PIN_JOY_X);

    attachInterrupt(digitalPinToInterrupt(PIN_ENC_CLK), encoderISR, CHANGE);
}

void loop() {
    readSlaveInput();
    readHornButton();
    readJoystickX();

    uint32_t currentTime = millis();
    if (currentTime - lastPcUpdate >= UPDATE_INTERVAL_MS) {
        lastPcUpdate = currentTime;
        sendPcPacket();
    }
}

void readHornButton() {
    uint8_t currentRead = digitalRead(PIN_ENC_SW);
    uint32_t currentTime = millis();
    if (currentRead != lastButtonRead) {
        lastDebounceTime = currentTime;
    }
    if ((currentTime - lastDebounceTime) > DEBOUNCE_DELAY_MS) {
        buttonState = (currentRead == LOW) ? 1 : 0;
    }
    lastButtonRead = currentRead;
}

void readJoystickX() {
    uint16_t rawX = analogRead(PIN_JOY_X);
    joyXFiltered = ((rawX * ADC_EMA_ALPHA) + (joyXFiltered * (256 - ADC_EMA_ALPHA))) >> 8;
}

void readSlaveInput() {
    while (slaveSerial.available() > 0) {
        char c = slaveSerial.read();
        if (c == '\n' || c == '\r') {
            if (rxIndex > 0) {
                rxBuffer[rxIndex] = '\0';
                parseSlavePacket(rxBuffer);
                rxIndex = 0;
            }
        } else if (c == '$') {
            rxBuffer[0] = '$';
            rxIndex = 1;
        } else if (rxIndex > 0 && rxIndex < (sizeof(rxBuffer) - 1)) {
            rxBuffer[rxIndex++] = c;
        }
    }
}

void parseSlavePacket(char* packet) {
    char* starPtr = strchr(packet, '*');
    if (starPtr == NULL) return; 
    
    uint8_t calculatedCs = 0;
    for (char* p = packet + 1; p < starPtr; p++) {
        calculatedCs ^= *p;
    }
    uint8_t receivedCs = (uint8_t)strtol(starPtr + 1, NULL, 16);
    if (calculatedCs != receivedCs) return;
    
    *starPtr = '\0';
    char* savePtr;
    char* token = strtok_r(packet, ",", &savePtr);
    if (!token || strcmp(token, "$SLV") != 0) return;
    
    token = strtok_r(NULL, ",", &savePtr); // seq
    if (!token) return;
    token = strtok_r(NULL, ",", &savePtr); // joyY
    if (!token) return;
    int16_t tempY = strtol(token, NULL, 10);
    
    token = strtok_r(NULL, ",", &savePtr); // accel
    if (!token) return;
    uint8_t tempAcc = strtol(token, NULL, 10);
    
    token = strtok_r(NULL, ",", &savePtr); // brake
    if (!token) return;
    uint8_t tempBrk = strtol(token, NULL, 10);
    
    token = strtok_r(NULL, ",", &savePtr); // clutch
    if (!token) return;
    uint8_t tempClu = strtol(token, NULL, 10);
    
    if (tempY >= 0 && tempY <= 1023 && tempAcc <= 1 && tempBrk <= 1 && tempClu <= 1) {
        slaveJoyY = tempY;
        slaveAccel = tempAcc;
        slaveBrake = tempBrk;
        slaveClutch = tempClu;
        lastSlaveTime = millis();
    }
}

void sendPcPacket() {
    noInterrupts();
    int32_t currentEncoder = encoderCount;
    interrupts();
    
    uint32_t slaveAgeMs = millis() - lastSlaveTime;
    int16_t activeJoyY = slaveJoyY;
    uint8_t activeAcc = slaveAccel;
    uint8_t activeBrk = slaveBrake;
    uint8_t activeClu = slaveClutch;
    
    if (slaveAgeMs > SLAVE_TIMEOUT_MS) {
        activeJoyY = JOY_Y_NEUTRAL;
        activeAcc = 0;
        activeBrk = 0;
        activeClu = 0;
    }
    
    uint16_t reportedAge = (slaveAgeMs > 65535) ? 65535 : (uint16_t)slaveAgeMs;
    
    char payload[90];
    snprintf(payload, sizeof(payload), "RIG,%lu,%ld,%u,%d,%u,%u,%u,%u,%u",
             pcSequenceNumber++,
             currentEncoder,
             joyXFiltered,
             activeJoyY,
             buttonState,
             activeAcc,
             activeBrk,
             activeClu,
             reportedAge);
             
    uint8_t cs = 0;
    for (uint8_t i = 0; payload[i] != '\0'; i++) {
        cs ^= payload[i];
    }
    
    Serial.printf("$%s*%02X\r\n", payload, cs);
}