/**
 * ESP8266 Racing Controller - Slave Firmware
 * Board: NodeMCU 1.0 (ESP-12E Module)
 */

#include <SoftwareSerial.h>

#define PIN_ACCEL       4  // D2 (GPIO4)
#define PIN_BRAKE       14 // D5 (GPIO14)
#define PIN_CLUTCH      5  // D1 (GPIO5)
#define PIN_JOY_Y       A0 // ADC0
#define PIN_RX          13 // D7 (GPIO13)
#define PIN_TX          12 // D6 (GPIO12)

const uint32_t SLAVE_BAUD_RATE      = 19200;
const uint32_t PC_BAUD_RATE         = 115200;
const uint32_t UPDATE_FREQ_HZ       = 100;
const uint32_t UPDATE_INTERVAL_MS   = 1000 / UPDATE_FREQ_HZ;
const uint32_t DEBOUNCE_DELAY_MS    = 20;

const uint16_t ADC_EMA_ALPHA        = 64; 
const uint16_t JOY_Y_NEUTRAL        = 512;

struct ButtonState {
    uint8_t pin;
    uint8_t raw;
    uint8_t stable;
    uint32_t lastToggleTime;
};

ButtonState btnAccel  = { PIN_ACCEL,  HIGH, 0, 0 };
ButtonState btnBrake  = { PIN_BRAKE,  HIGH, 0, 0 };
ButtonState btnClutch = { PIN_CLUTCH, HIGH, 0, 0 };

uint16_t joyYFiltered = JOY_Y_NEUTRAL;
uint32_t sequenceNum  = 0;
uint32_t lastTxTime   = 0;

SoftwareSerial masterSerial(PIN_RX, PIN_TX);

void setup() {
    masterSerial.begin(SLAVE_BAUD_RATE);

    pinMode(btnAccel.pin, INPUT_PULLUP);
    pinMode(btnBrake.pin, INPUT_PULLUP);
    pinMode(btnClutch.pin, INPUT_PULLUP);

    joyYFiltered = analogRead(PIN_JOY_Y);

    btnAccel.raw  = digitalRead(btnAccel.pin);
    btnBrake.raw  = digitalRead(btnBrake.pin);
    btnClutch.raw = digitalRead(btnClutch.pin);
}

void loop() {
    uint32_t currentTime = millis();

    processButton(btnAccel, currentTime);
    processButton(btnBrake, currentTime);
    processButton(btnClutch, currentTime);
    processADC();

    if (currentTime - lastTxTime >= UPDATE_INTERVAL_MS) {
        lastTxTime = currentTime; 
        transmitPacket();
    }
}

void processButton(ButtonState &btn, uint32_t currentTime) {
    uint8_t currentRead = digitalRead(btn.pin);
    if (currentRead != btn.raw) {
        btn.lastToggleTime = currentTime;
        btn.raw = currentRead;
    }
    if ((currentTime - btn.lastToggleTime) >= DEBOUNCE_DELAY_MS) {
        btn.stable = (btn.raw == LOW) ? 1 : 0;
    }
}

void processADC() {
    uint16_t rawY = analogRead(PIN_JOY_Y);
    joyYFiltered = ((rawY * ADC_EMA_ALPHA) + (joyYFiltered * (256 - ADC_EMA_ALPHA))) >> 8;
}

void transmitPacket() {
    char payload[64];
    snprintf(payload, sizeof(payload), "SLV,%lu,%u,%u,%u,%u",
             sequenceNum++,
             joyYFiltered,
             btnAccel.stable,
             btnBrake.stable,
             btnClutch.stable);

    uint8_t cs = 0;
    for (uint8_t i = 0; payload[i] != '\0'; i++) {
        cs ^= payload[i];
    }

    masterSerial.printf("$%s*%02X\n", payload, cs);
}