# DIY PC Racing Controller

A custom dual-ESP8266 racing controller featuring a steering rotary encoder, analog H-pattern shifter, and digital accelerator, brake, and clutch pedals.

The system includes a Python/PySide6 desktop dashboard for live telemetry, steering calibration, gear mapping, and virtual Xbox 360 controller output on Windows.

## Features

- Custom steering wheel with rotary encoder input
- Analog H-pattern shifter
- Digital accelerator, brake, and clutch pedals
- Dual ESP8266 NodeMCU architecture
- Master–Slave serial communication
- Live telemetry monitoring
- Steering center calibration
- Quick gear mapping
- Virtual Xbox 360 controller output
- Windows desktop application

## 1. Download the Required Files

Open the project's **Releases** section on GitHub and download these three items from **Release 1.7.0**:

| File | Purpose |
|---|---|
| `setup.bat` | Configures the required software environment |
| Main application `.exe` | Launches the desktop dashboard |
| Firmware files (`.ino`) | Contains the Arduino sketches for both ESP8266 boards |

**Important:** Download all three items from the same release to maintain compatibility.

## 2. Installation and Setup

Follow these steps in the specified order.

### Step 1: Run `setup.bat`

1. Download `setup.bat` from Release 1.7.0.
2. Place it in a suitable folder on your Windows PC.
3. Run `setup.bat`.
4. Allow the script to complete the required setup.
5. Follow any on-screen instructions and resolve reported errors before continuing.

### Step 2: Flash the Firmware

The system uses two identical ESP8266 NodeMCU boards. Each board runs a different Arduino sketch.

**Master ESP8266 — Steering Controller**

1. Open `master.ino` in the Arduino IDE.
2. Ensure ESP8266 board support and the required libraries are installed.
3. Connect the Master board to your PC using USB.
4. Select the appropriate ESP8266 NodeMCU board and its COM port.
5. Click **Upload** and wait for the process to finish.

**Slave ESP8266 — Pedals and Shifter**

1. Open `slave.ino` in the Arduino IDE.
2. Connect the Slave board to your PC using USB.
3. Select the appropriate ESP8266 NodeMCU board and the Slave's COM port.
4. Click **Upload** and wait for the process to finish.

**Firmware precautions:**

- Flash `master.ino` to the Master and `slave.ino` to the Slave.
- Do not interchange the two sketches.
- Install any required libraries specified by the firmware.
- Ensure the sketches use the same serial baud rate: **19200 baud**.
- Close the desktop application or any other program using the selected COM port before flashing.

### Step 3: Complete the Hardware Connections

Disconnect power before changing wiring. Follow the connection tables in the next section.

Verify the pin assignments and analog input voltage limits before powering on the assembled controller.

### Step 4: Launch the Application

1. Connect the Master ESP8266 to the PC using USB.
2. Run the main application `.exe` downloaded from Release 1.7.0.
3. Select the **Master ESP8266 COM port**.
4. Click **Connect**.
5. Turn the steering wheel and verify that telemetry responds.
6. Click **Set Current Position as Center** to calibrate steering.
7. Use **Quick Gear Mapping** to map the physical shifter positions to virtual gears.
8. Test the accelerator, brake, and clutch inputs.
9. Enable **Enable Game Controls** when the controller is ready for use.

---

## 3. Hardware Architecture

The system uses two identical ESP8266 NodeMCU boards with different firmware and responsibilities.

| Board | Responsibilities |
|---|---|
| Master ESP8266 | Reads steering encoder and joystick input, receives Slave telemetry, and communicates with the PC |
| Slave ESP8266 | Reads accelerator, brake, clutch, and analog shifter inputs and transmits their states to the Master |

Although the boards use the same hardware, they must run their respective firmware sketches.

## 4. Master ESP8266 — Steering and Joystick

### A. Steering Rotary Encoder

Connect the steering encoder to the Master ESP8266 as follows:

| Encoder Pin | Master ESP8266 Pin |
|---|---|
| CLK | D5 |
| DT | D6 |
| SW | D7 |
| + / VCC | 3V3 |
| − / GND | GND |

The CLK and DT signals provide the rotary encoder's movement and direction information. The SW pin is the encoder's push-button input.

### B. Analog Joystick

| Joystick Pin | Master ESP8266 Pin |
|---|---|
| VRX | A0 |
| VCC | 3V3 |
| GND | GND |

The VRX signal provides the analog input used by the firmware for its assigned function.

## 5. Slave ESP8266 — Pedals and H-Pattern Shifter

### A. Digital Pedal Buttons

The three digital buttons represent the accelerator, brake, and clutch.

| Pedal | Button Label | Slave ESP8266 Pin |
|---|---|---|
| Accelerator | A | D1 |
| Brake | B | D2 |
| Clutch | C | D5 |

Each button is read as a digital input by the Slave firmware.

Configure the input pull-up or pull-down logic to match the actual button wiring. If using normally open buttons with `INPUT_PULLUP`, a released button typically reads `HIGH` and a pressed button reads `LOW`.

### B. Analog H-Pattern Shifter

| Shifter / Joystick Pin | Slave ESP8266 Pin |
|---|---|
| VRY | A0 |
| VCC | 3V3 |
| GND | GND |

The VRY signal provides the analog position reading used to determine the selected gear.

Use **Quick Gear Mapping** in the desktop dashboard to associate physical shifter positions with the corresponding virtual gear regions.

## 6. Master–Slave Serial Communication

Connect the two ESP8266 boards using the following wiring.

| Master ESP8266 | Slave ESP8266 |
|---|---|
| D2 (RX) | D6 (TX) |
| D1 (TX) | D7 (RX) |
| GND | GND |

The UART connections are crossed: the Master RX connects to the Slave TX, and the Master TX connects to the Slave RX.

Both firmware sketches must use the same baud rate: **19200 baud**.

The Slave transmits pedal and shifter telemetry to the Master. The Master communicates with the desktop application over USB serial.

**Note:** Verify that the firmware actually configures these pins for UART or compatible software serial. Default hardware UART pin assignments can differ from the pins listed above.

## 7. Power and Ground

- Connect each module's GND to the GND of its respective ESP8266.
- Connect the Master and Slave grounds together.
- Power compatible modules from the appropriate 3.3V supply.
- Never apply 5V directly to ESP8266 GPIO pins.
- Check the analog input voltage limit for A0 on your specific NodeMCU board.
- Disconnect power before modifying the wiring.
- Ensure the power supply can handle the combined current requirements of the connected modules.

## 8. Dashboard Operation

### Connect to the Controller

1. Connect the Master ESP8266 to the PC.
2. Select its COM port.
3. Click **Connect**.
4. Confirm that telemetry updates correctly.

The Slave communicates with the Master and does not need its own PC connection during normal operation.

### Calibrate Steering

1. Keep the steering wheel in the desired center position.
2. Click **Set Current Position as Center**.
3. Turn the wheel in both directions.
4. Confirm that the steering readings change smoothly and in the correct direction.

If the steering range is incorrect, check the encoder resolution and the firmware or application configuration.

### Map the Gears

1. Open **Quick Gear Mapping**.
2. Move the physical shifter into each gear position.
3. Assign the corresponding virtual gear region.
4. Verify that each physical position produces the intended gear reading.

### Enable Game Controls

Enable **Enable Game Controls** only after checking steering, gears, and pedals.

The application must have a compatible virtual gamepad output implementation and any required driver installed. Verify that Windows recognizes the virtual controller before launching a racing game.

---

## 9. Troubleshooting

### Controller Not Detected

- Select the COM port belonging to the Master ESP8266.
- Check that the USB cable supports data.
- Verify that the USB-to-serial driver is installed.
- Close other applications using the COM port.
- Confirm that the Master firmware uploaded successfully.

### Steering Barely Registers

- Check the encoder wiring.
- Verify the encoder's actual counts per revolution.
- Check the configured steering scaling, including `counts_per_degree` if used by the application.
- Confirm that the firmware reports changing encoder counts.

Do not assume all rotary encoders have the same resolution. Encoder counts depend on the device, decoding method, and mechanical arrangement.

### Slave Lag or High Telemetry Age

- Check the Master D2/D1 connections to the Slave D6/D7 pins.
- Verify that both sketches use **19200 baud**.
- Ensure that both boards share a common ground.
- Confirm that the Slave is transmitting the expected telemetry format.
- Inspect the serial implementation for timing conflicts or dropped data.

### Pedal Stuck at `1`

- Inspect the pedal button's common, normally open (NO), and normally closed (NC) terminals.
- For a normally open button using `INPUT_PULLUP`, the released state is usually `HIGH` (`1`) and the pressed state is `LOW` (`0`).
- Check that the firmware uses the correct pin and input logic.
- Do not assume the input is faulty until the wiring and pull-up configuration have been verified.

### Incorrect Shifter Readings

- Check the VRY, VCC, and GND connections.
- Confirm that the analog input remains within the permitted voltage range.
- Check the raw analog readings for each gear position.
- Repeat Quick Gear Mapping after correcting the wiring or calibration.

### Virtual Controller Not Detected

- Enable **Enable Game Controls** in the application.
- Verify that the required virtual gamepad driver or library is installed.
- Confirm that Windows recognizes the virtual controller.
- Check application permissions and any driver installation errors.
- Test the controller before opening the racing game.

---

## 10. Recommended Startup Checklist

- [ ] Download `setup.bat`, the main `.exe`, and both `.ino` firmware sketches from Release 1.7.0.
- [ ] Run `setup.bat` and confirm that setup completes.
- [ ] Flash `master.ino` to the Master ESP8266.
- [ ] Flash `slave.ino` to the Slave ESP8266.
- [ ] Complete and verify the hardware wiring.
- [ ] Confirm common ground and safe analog input voltages.
- [ ] Connect the Master to the PC.
- [ ] Launch the main application `.exe`.
- [ ] Connect to the Master COM port.
- [ ] Calibrate steering and map the gears.
- [ ] Test the accelerator, brake, and clutch.
- [ ] Enable virtual gamepad output and verify operation in Windows.

## Safety and Compatibility Notes

- The connection tables describe the intended wiring and must match the firmware.
- Confirm the exact NodeMCU board variant and its A0 input range before connecting analog signals.
- Confirm that the selected serial implementation supports the specified Master and Slave pins.
- Use only compatible low-voltage power sources for the ESP8266 and attached modules.
- Install the firmware and application from the same release whenever possible.

**Enjoy your custom racing controller!**
