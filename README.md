# Helmholtz Coil Control System


## Overview

This branch contains code used to control and calibrate the Helmholtz coil system, designed for manipulating magnetic microrobots. It includes scripts for camera-based visualization, serial communication, Arduino PWM control, and automated calibration.

## Contents

* `camera.py` – Live video feed and recording of workspace for positioning and experiment tracking.
* `serial_interface.py` – Interface to send custom current commands to Arduino via serial communication.
* `serial_cal_test.py` – Automated script to incrementally increase current for magnetic field calibration.
* `modifiedPWM.ino` – Arduino code with calibrated parameters to generate PWM signals for coil current control.
* `originalPWM.ino` – The legacy version of the Arduino control script, preserved for reference.

## System Overview

This system allows for:

* **Precise control of four independent coil channels** (MX, HX, MY, HY) in a Helmholtz configuration.
* **Live visualization** for manual microrobot positioning.
* **Recording and playback** of microrobot movement.
* **Calibrated PWM output** to ensure accurate current delivery.
* **Automated current sweep** to aid in creating calibration curves using a Gaussmeter.

## `camera.py`

### Description

* Opens a live video feed from a connected USB camera.
* Press `r` to **start/stop recording**.
* Press `q` or `Esc` to **exit**.
* After recording, you will be prompted to **save or discard** the video.
* Playback supports pausing (`space`), seeking, and review.

### Use Case

Used during field measurement experiments to ensure correct **probe placement** and **microrobot movement tracking**.

### Requirements

* Python 3
* OpenCV (`pip install opencv-python`)

### Run

```bash
python camera.py
```

## `serial_cal_test.py`

### Description

* Connects to an Arduino via serial.
* Requests initial current values for coils.
* Automatically increments the HY channel by **+0.5A every 3 seconds** until it reaches 10A.
* Useful for **generating calibration curves** using Gaussmeter measurements.

### Example Use

```bash
python serial_cal_test.py
```

When prompted, enter:

```
0, 0, 0, 0
```

### Requirements

* Python 3
* `pyserial` (`pip install pyserial`)

## `serial_interface.py`

### Description

A manual interface to send current values to the Arduino over serial. Supports values for MX, HX, MY, and HY.

### Example Command

```
Enter currents (e.g. 3.0, 1.5, -2.0, 0.5): 
```

### Use Case

Used for **manual testing** and **real-time control** of the Helmholtz coil system.

### Run

```bash
python serial_interface.py
```

## `modifiedPWM.ino`

### Description

* Arduino sketch for **PWM-based current control** of 4 coil drivers: MX, HX, MY, and HY.
* Contains **calibrated slope, intercept, and current compensation factors** for HX, HY channels.
* Reads serial input, parses current commands, and sets the appropriate PWM output.
* Designed for **Arduino Mega 2560**.

### Input Format

```text
3.0, 1.5, -2.0, 0.5
```

Each value corresponds to the desired current (in Amps) for:
`MX`, `HX`, `MY`, `HY`

### Output

PWM values are automatically calculated and set on appropriate motor pins, considering direction and calibration.

## `originalPWM.ino`

### Description

* Original PWM control code used in a **previous student project**.
* Retained here for **reference and comparison**.
* Not recommended for use in this calibrated system.

## Dependencies

* **Hardware**:

  * Arduino Mega 2560
  * Power drivers for coil control
  * USB camera
  * Gaussmeter (for calibration)
* **Python Libraries**:

  * `pyserial`
  * `opencv-python`


## Setup

1. Connect Arduino via USB to your computer.
2. Upload `modifiedPWM.ino` to your Arduino Mega 2560.
4. Launch `serial_interface.py` or `serial_cal_test.py` as needed.
5. Use `camera.py` for visual monitoring and recording.


## Notes

* Ensure correct COM port is used in `serial_interface.py` and `serial_cal_test.py`. Modify `PORT = 'COM3'` if needed.
* All current commands are expected in **Ampere** units.
* Calibrations are based on empirical measurements and may need adjustment for hardware changes.
