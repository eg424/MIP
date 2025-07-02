# Helmholtz Coil Control System


## Overview

This branch contains code used to control and calibrate the Helmholtz coil system, designed for manipulating magnetic microrobots. It includes scripts for camera-based visualization, serial communication, Arduino PWM control, and automated calibration.

## Contents

* `serial_cam.py` – Unified interface for sending coil current values and automatically recording the camera feed with synchronized control.
* `camera.py` – Live video feed and recording of workspace for positioning and experiment tracking.
* `serial_interface.py` – Interface to send custom current commands to Arduino via serial communication.
* `serial_cal_test.py` – Automated script to incrementally increase current for magnetic field calibration.
* `modifiedPWM.ino` – Arduino code with calibrated parameters to generate PWM signals for coil current control.
* `originalPWM.ino` – The legacy version of the Arduino control script, preserved for reference.

### Testing Scripts

* `seq1.py` - Repeatedly sends a fixed sequence of coil current commands to Hx, Hy with 0.5-second delays.

## System Overview

This system allows for:

* **Precise control of four independent coil channels** (MX, HX, MY, HY) in a Helmholtz configuration.
* **Live visualization** for manual microrobot positioning.
* **Recording and playback** of microrobot movement.
* **Calibrated PWM output** to ensure accurate current delivery.
* **Automated current sweep** to aid in creating calibration curves using a Gaussmeter.

## `serial_cam.py`

### Description

An integrated script that **automatically begins recording** video as soon as new current values are sent over serial. This combines the functionality of both `serial_interface.py` and `camera.py` into a **synchronized control-recording system**.

### Key Features

- **Automatic recording**: Starts video capture immediately after sending current input values to the Arduino.
- **Input-based filename**: Recordings are saved with the user-inputted current values and a timestamp.
- **Real-time camera display** with a "REC" overlay.
- **Interactive playback mode**:
  - `q` or `Esc`: View last recording.
  - `space`: Pause/resume.
  - `s`: Save recording.
  - `n`: Discard recording.
- **PWM zeroing mode**: Pressing `r` stops recording and sends `0,0,0,0` repeatedly over serial to safely idle the coils.
- **Clean exit** with proper release of serial, video, and GUI resources.

### Input Format

* User is prompted for: MX, HX, MY, HY
* Example input: 2.0, 1.5, -2.0, 0.5
* This command is sent to the Arduino, and recording begins automatically.

### Controls

| Key        | Action                                       |
|------------|----------------------------------------------|
| `r`        | Stop recording and enter zero-current mode   |
| `q` / `Esc`| Playback last recording / Exit playback mode |
| `s`        | Save current playback video                  |
| `n`        | Discard current playback video               |
| `space`    | Toggle pause/play during playback            |


## `camera.py`

### Description

* Opens a live video feed from a connected USB camera.
* Press `r` to **start/stop recording**.
* Press `q` or `Esc` to **stop and review** the most recent recording.
* After recording, the video will automatically **play back** with support for:
  * Pause/resume with `space`
  * Seeking using a trackbar
  * Save the recording with `s`
  * Discard the recording with `n`
 
### Key Features
* Real-time frame capture with consistent playback speed.
* Overlay showing current state (PLAY / PAUSE) and elapsed time.
* Frame-accurate navigation and saving option after each recording.

### Use Case

Used during field measurement experiments to ensure correct **probe placement** and **microrobot movement tracking**.

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

## `serial_interface.py`

### Description

* A manual interface to send current values to the Arduino over serial. Supports values for MX, HX, MY, and HY.
* Can be used simultaneously with `camera.py` to manually record how the module reacts to different inputs.

### Example Command

```
Enter currents (e.g. 3.0, 1.5, -2.0, 0.5): 
```

### Use Case

Used for **manual testing** and **real-time control** of the Helmholtz coil system.


## `seq1.py`

### Description
* Connects to the serial port COM3 at 9600 baud.
* Sends the following patterns repeatedly:
  * [0, 1, 0, 0]
  * [0, 0, 0, 0] (reset)
  * [0, 0, 0, 1]
  * [0, 0, 0, 0] (reset)

* Prints the command sent to the console for logging.
* Waits 0.5 seconds between each command.

---

## `Helmholtz.ino`

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
2. Upload `Helmholtz.ino` to your Arduino Mega 2560.
3. Use `serial_cam.py` for unified control and recording of modules.
4. Launch `serial_cal_test.py` if needed, for automated current sweeps.
5. Optionally, use `camera.py` or `serial_interface.py` if needed.


## Notes

* Ensure correct COM port is used in `serial_interface.py` and `serial_cal_test.py`. Modify `PORT = 'COM3'` if needed.
* All current commands are expected in **Ampere** units.
* Calibrations are based on empirical measurements and may need adjustment for hardware changes.