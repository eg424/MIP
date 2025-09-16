# Design and Control of Modular Magnetic Millirobots for Multimodal Locomotion, Shape Reconfiguration and Grasping
<div align="center">
<img width="1185" height="1116" alt="image" src="https://github.com/user-attachments/assets/8b2384aa-344d-4957-ba02-058138c889a5" />
</div>

## Overview

The project presents a modular magnetic millirobotic platform capable of:
- **Single-module locomotion** using Helmholtz and Maxwell coil inputs.
- **Multimodal reconfiguration** into chains, squares, and grippers.
- **Closed-loop navigation** with real-time vision feedback and A* path planning.  
All functions are achieved at **low magnetic field strengths (<13 mT)** using a compact **2-D electromagnetic setup**.

The framework consists of three layers:

1. **Arduino firmware** for low-level current control of electromagnetic coils.
2. **Python framework** for experiment orchestration, computer vision, recording, and autonomous path planning.
3. **MATLAB tools** for post-processing and statistical analysis of recorded trajectories.

## Key Features

- **Magnetic actuation control** via serial communication with external drivers.  
- **Vision-based module detection** (`moduleDetection.py`) using OpenCV for real-time tracking.  
- **Finite State Machine (FSM)** (`FiniteStateMachine.py`) for handling motion commands and transformations.  
- **Path planning mode** with goal setting and automated trajectory visualization.  
- **Sequence execution** (`Sequences/`) for predefined current input patterns.  
- **Automated recording and analysis** with trajectory overlays, merge detection, and reconfiguration logging.

## Repository Structure

```
MIP/
├── Arduino/
│   ├── EMS.ino # Arduino code for coil current control
│   └── originalPWM.ino # Legacy version
├── MATLAB/
│   ├── Trials/ # Raw trial data
│   ├── DataAnalysis.m # Post-processing and plotting
│   ├── *.png / *.xlsx # Analysis figures and datasets
├── Python/
│   ├── Images/ # Module configuration dataset
│   ├── Basic Interfacing/ # Camera, calibration, serial tools
│   ├── Sequences/  # Predefined coil actuation sequences
│   ├── main.py # Main entry point (control + recording)
│   ├── pathPlanning.py # Path planning and trajectory execution
│   ├── FiniteStateMachine.py # FSM for command-based motion simulation
│   ├── moduleDetection.py # Vision-based module detection and tracking
│   ├── README.md # Project documentation
```

## Hardware Setup

* **Modular robot platform** with electromagnetic coil actuation.
* **Arduino** microcontroller controlling 4 coil channels.
* **USB camera** for live vision-based tracking.
* **DC power supply** with current-limiting enabled (safety-critical).
* **Gaussmeter** (optional) for magnetic field calibration.

> **Safety:** Ensure coil currents do not exceed **10 A** on HX/HY channels. Always enable current limiting on the power supply.


## Software Requirements

* **Arduino IDE** (to flash `EMS.ino`)
* **Python 3.9+** with:

  * `opencv-python`
  * `numpy`
  * `matplotlib`
  * `pyserial`
* **MATLAB** (for analysis & plotting)

Install Python dependencies with:

```bash
pip install -r requirements.txt
```

## Workflow

### 1. Upload Firmware

Flash `Arduino/EMS.ino` to the Arduino board. This program receives serial commands to set coil currents.

### 2. Calibrate Fields

Use `Python/Basic Interfacing/fieldCalibration.py` to generate calibration curves with a gaussmeter. Alternatively, `serial_interface.py` provides direct manual current control.

### 3. Run Experiments

Launch:

```bash
python Python/main.py
```

Features include:

* **Manual control**: enter custom current values.
* **Predefined sequences**: run stored coil actuation sequences.
* **Autonomous path planning**: select goals in live workspace view; system computes A\* path and executes movements.

### 4. Recording & Replay

* All experiments can be recorded (AVI format).
* Trajectories and merge/reconfiguration events are detected automatically.
* After each run, playback allows saving/discarding videos and generating trajectory overlays.

### 5. Data Analysis

Run MATLAB analysis with:

```matlab
DataAnalysis.m
```

This script:

* Loads CSV files generated during experiments.
* Computes statistics across experiments.
* Generates publication-ready plots (e.g., displacement, trajectory variance, time to merge).

## Example Experiment

1. **Upload firmware** to Arduino.
2. **Start main control**:

   ```bash
   python Python/main.py
   ```
3. **Select a sequence** (e.g., `seq1`) or enter manual currents.
4. **Record and replay** the experiment.
5. **Save trajectory outputs** (PNG overlays, merge/reconfiguration logs).
6. **Analyze results in MATLAB** with `DataAnalysis.m`.

## Outputs

Each experiment can produce:

* **Videos (AVI)** – raw and annotated recordings.
* **Trajectory plots (PNG)** – full and interval-based overlays.
* **Merge/reconfiguration logs (TXT)** – timing of module interactions.
* **CSV files** – displacement, centroid coordinates, and experimental metadata.
* **MATLAB figures** – summary statistics and comparative plots.
