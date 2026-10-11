# DIY PC Racing Controller

A fully custom, dual-ESP8266 racing controller system supporting a steering encoder, H-pattern analog shifter, and digital pedals. Features a Python/PySide6 desktop dashboard for live telemetry, visual calibration, and virtual gamepad output.

## Installation & Setup

1. **Hardware Assembly:**
   * Flash `master.ino` to the Steering ESP8266.
   * Flash `slave.ino` to the Pedals ESP8266.
   * Connect Master `D2 (RX)` to Slave `D6 (TX)` and Master `D1 (TX)` to Slave `D7 (RX)`.
   * **Crucial:** Ensure both ESP8266 boards and all sensors share a common Ground (GND).
   * Power modules from the 3.3V pin (do not apply 5V directly to ESP8266 GPIOs).

2. **Python Environment:**
   * Require Python 3.10+
   * `python -m venv venv`
   * `venv\Scripts\activate`
   * `pip install -r requirements.txt`

3. **Running the Dashboard:**
   * `python main.py`
   * Select the Master ESP8266 COM port and click **Connect**.
   * Turn the steering wheel and click **Set Current Position as Center**.
   * Use the **Quick Gear Mapping** to assign your physical shifter slots to virtual H-pattern regions.
   * Check **Enable Game Controls** to begin piping telemetry to Windows as a virtual Xbox 360 controller.

## Troubleshooting

* **Controller Not Detected:** Ensure you are selecting the Master board's COM port. The Slave board communicates only with the Master, not the PC.
* **Steering Barely Registers:** Adjust `counts_per_degree` in `main.py`. A standard KY-040 outputs ~30 counts per revolution (`0.08333`), whereas high-res optical encoders output 600+ (`1.666`).
* **Slave Lag / High Age (ms):** Check the jumper wires between Master D2/D1 and Slave D6/D7. Ensure the baud rate is matched at 19200 in both sketches.
* **Floating Pedals (Stuck at 1):** Check the pedal switch wiring. If a pedal constantly reads `1` when released, it is wired to the `Normally Closed (NC)` pin. Move the wire to the `Normally Open (NO)` pin.