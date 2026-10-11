# DIY PC Racing Controller System

A professional, high-performance, standalone dual-ESP8266 custom racing controller suite. This system reads high-frequency rotation telemetry from an optical or mechanical rotary encoder (steering wheel), manages precise H-pattern gear shifts via an analog joystick, processes digital pedal inputs, and interfaces seamlessly with Windows as a native virtual Xbox 360 controller (`vgamepad`) or keyboard macro layout.

---

## 🛠️ System Architecture & Hardware Specifications

```
+-------------------------------------------------------------------------+
|                        PC HOST (Windows 10/11)                          |
|  - PyQt6 / PySide6 Interactive Dashboard & Auto-Calibration Wizard      |
|  - Central Mapping Engine & JSON Profile Persistence (My Documents)     |
|  - vgamepad (ViGEmBus Virtual Xbox 360 Driver Interface)                |
+-----------------------------------^-------------------------------------+
                                    | USB Serial (115200 Baud)
                                    | Telemetry Packets & Checksum Verification
+-----------------------------------+-------------------------------------+
|                      MASTER ESP8266 (Steering & Hub)                    |
|  - KY-040 / Rotary Encoder Input (GPIO Pins)                            |
|  - Aggregates Master telemetry and polls Slave via SoftwareSerial       |
+-----------------------------------^-------------------------------------+
                                    | SoftwareSerial (19200 Baud)
                                    | Master D2(RX) <---> Slave D6(TX)
                                    | Master D1(TX) <---> Slave D7(RX)
+-----------------------------------+-------------------------------------+
|                      SLAVE ESP8266 (Pedals & Shifter)                   |
|  - PS2-Style Analog Joystick (X/Y Axis for H-Pattern Region Mapping)   |
|  - Digital Microswitches / Pushbuttons (Accelerator, Brake, Clutch, Horn)|
+-------------------------------------------------------------------------+
```

### Hardware Pinout & Wiring Blueprint

1. **Power Management:** 
   * Power both ESP8266 development boards and all peripheral sensors strictly via regulated **3.3V** rails. **Do not apply 5V directly to ESP8266 GPIO pins**, as they are not 5V tolerant.
   * Ensure a **Common Ground (GND)** is shared across the Master ESP8266, Slave ESP8266, encoder, joystick, and all pedal switches.

2. **Master-to-Slave UART Bridge:**
   * **Master D2 (RX)** $\longleftrightarrow$ **Slave D6 (TX)**
   * **Master D1 (TX)** $\longleftrightarrow$ **Slave D7 (RX)**
   * Baud Rate: **19200** configured for internal packet polling to maintain a sub-100ms slave age latency.

3. **Steering Hardware (Master):**
   * Rotary Encoder (KY-040 or high-res optical): Connected to dedicated interrupt pins on the Master ESP8266. Default mechanical encoders yield roughly 30–40 counts per 360-degree rotation (ratio: $0.08333$ counts/degree).

4. **Pedals & Shifter Hardware (Slave):**
   * **PS2 Joystick:** Analog X and Y connected to ADC/analog multiplexing lines for continuous H-pattern region tracking.
   * **Pedals (Accelerator, Brake, Clutch):** Connect switches to the **Normally Open (NO)** pins. (Wiring to NC will invert logic and lock pedals permanently at 100%).

---

## 🚀 Installation & Setup Guide

### Step 1: Pre-requisites & Windows Drivers
1. **ViGEmBus Driver:** Because the desktop application emulates a native Xbox 360 controller using `vgamepad`, the host Windows machine must have the kernel-level **Nefarius ViGEmBus Driver** installed. Download and install the latest release from the official repository before launching game controls.
2. **Python Environment:** Ensure Python 3.10 or higher is installed and added to your Windows PATH.

### Step 2: Flashing Firmware
1. Open your Arduino IDE.
2. Install the `ESP8266 Board Package` via Board Manager.
3. Flash `master.ino` to the Steering ESP8266 and `slave.ino` to the Pedals/Shifter ESP8266. Verify baud rates match (`115200` for PC Serial, `19200` for SoftwareSerial).

### Step 3: Application Setup & Running from Source
If you are running the source code directly within your workspace:
1. Open a terminal in the project root folder.
2. Create and activate a clean virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. Install all required dependencies:
   ```powershell
   pip install PySide6 vgamepad pyserial pyinstaller
   ```
4. Launch the dashboard:
   ```powershell
   python main.py
   ```

---

## 📦 Building a Standalone Executable & Installer

To package the application into a standalone `.exe` that runs from any folder on your machine or a USB drive without requiring a local Python installation:

1. **Automated Build:** Use the provided **`build_and_setup.bat`** script in the project root. Double-clicking this script will automatically create a temporary virtual environment, compile all dependencies, embed the application icon (`icon.ico`), and output a portable single-file executable to the `dist/` folder.
2. **Global Integration (`setup.bat`):** Run the **`setup.bat`** script to automatically register the application to your Windows PATH environment variable and generate a clean desktop shortcut, allowing you to trigger `DIY Racing Controller.exe` from any terminal command line worldwide.

---

## ⚙️ Calibration & Configuration

### 1. Steering Calibration Wizard
* **Center Calibration:** Point your physical steering wheel straight ahead, connect your Master COM port, and click **"Set Current Position as Center"**.
* **360° Auto-Calibration:** Click **"Auto-Calibrate 360° Rotation"**. Follow the two-step prompt: hold steady at step 1, turn the wheel exactly one full physical rotation (360°) at step 2, and click OK. The engine automatically computes your exact hardware counts-per-degree ratio.
* **Soft Locks:** Adjust the **Max Angle Spinner** on the fly (e.g., set to $450^\circ$ for Euro Truck Simulator 2, or $90^\circ$ for high-sensitivity open-wheel racing). The overtravel safety net clamps output coordinates at $\pm1.0$ while preserving hidden mechanical counts.

### 2. Quick H-Pattern Gear Mapping
1. Push your physical shifter joystick firmly into a target slot (e.g., Top-Left for Gear 1).
2. Click the corresponding **"Set Gear [X]"** button on the dashboard.
3. The engine draws an adaptive bounding box ($X \pm 0.15, Y \pm 0.20$) around your exact live coordinates and renders them on the live visualizer overlay.
4. Go to the **Settings & Profiles** tab and click **"Save Settings & Gear Map to Profile"**. Profiles are stored safely inside your user documents (`Documents/DIY Racing Controller/profiles/default_profile.json`) to bypass Windows Program Files permission restrictions.

---

## 🎮 In-Game Integration (e.g., Euro Truck Simulator 2 / Assetto Corsa)

1. **Connect:** Open the Dashboard, select your Master ESP8266 COM port, and click **Connect**.
2. **Activate Virtual Gamepad:** Check the **"Enable Game Controls"** checkbox. This initializes the `vgamepad` adapter, exposing your rig to Windows as an Xbox 360 controller.
3. **Game Bindings:**
   * **Steering:** Bind in-game steering directly to the **Left Joystick X-Axis**.
   * **Gears:** Map your custom H-pattern gear regions to keyboard buttons or gamepad bindings within the mapping engine.
   * **Pedals & Horn:** Map your digital momentary switches to Gamepad Face Buttons (`A` for Accelerator, `B` for Brake, `Y` for Clutch, `X` for Horn). *Tip: In simulator options, lower your acceleration/braking sensitivity sliders to smooth out digital on/off inputs.*

---

## 🔍 Troubleshooting Guide

* **`ModuleNotFoundError` or DLL Load Failures:** Ensure you are executing builds from an active virtual environment where all required libraries (`PySide6`, `vgamepad`, `pyserial`) are fully installed.
* **Slave Lag / High Age (>100ms):** Inspect physical wiring connections between Master pins `D2/D1` and Slave pins `D6/D7`. Ensure baud rates match on both microcontrollers.
* **Pedals Stuck at 100%:** Your pedal switch is wired to the **Normally Closed (NC)** terminal. Move the signal wire over to the **Normally Open (NO)** pin.
* **Steering Not Registering Full Range:** Run the 360° Auto-Calibration wizard or manually tune the `counts_per_degree` ratio in your profile settings.
