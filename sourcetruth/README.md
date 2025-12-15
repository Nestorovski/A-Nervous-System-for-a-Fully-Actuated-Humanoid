# Robot Studio: Universal Control Platform

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Universal-green)
![Architecture](https://img.shields.io/badge/Architecture-Distributed%20I2C-orange)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**Robot Studio** is a production-grade control engine designed to solve the "4-motor limit" of standard robotics shields. By utilizing a distributed I2C architecture, this platform allows a single Arduino Mega to control **42+ actuators** (DC Motors with feedback & Servos) simultaneously with smooth interpolation and physics-aware visualization.

> **Read the full story:** [Scaling Up: A "Nervous System" for a Fully Actuated Humanoid](LINK_TO_YOUR_ARTICLE) <<<CHANGE THIS

---

## Key Features

* **Distributed Hub-and-Spoke Topology:** Controls actuators via a TCA9548A Multiplexer and local "IvanModules", reducing cabling complexity.
* **Ghost-Lead Synchronization:** The software controls a virtual "Ghost" robot; a PID control loop forces the physical robot to mimic the Ghost in real-time.
* **Engineer Mode:** Live hardware diagnostics, I2C bus scanning, and hot-swappable pin mapping without recompiling firmware.
* **Universal Architecture:** Defined entirely by JSON. The same engine runs an InMoov Humanoid, a Hexapod, or a Rover.
* **Animation Sequencer:** Record, play, and smooth keyframe animations.

---

## Hardware Requirements

The system relies on a custom distributed stack:

* **Master:** 1x Arduino Mega 2560
* **Router:** 1x TCA9548A I2C Multiplexer (Addr 0x70)
* **Nodes (IvanModules):** 7x Custom Boards containing:
  * 1x PCA9685 PWM Driver
  * 1x ADS1115 ADC (for Potentiometer feedback)
  * 2x TB6612FNG Dual Motor Drivers
* **Actuators:** N20 DC Motors (12V) and SG90 Servos.

---

## Installation

### 1. Python Environment

Ensure you have Python 3.10 or newer installed.

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/inmoov-studio.git <<<CHANGE THIS
cd inmoov-studio <<<CHANGE THIS

# Install dependencies
pip install PyQt6 pyserial numpy pyqtgraph PyOpenGL
```

### 2. Arduino Firmware

1. Open `arduino_code/ivan_universal.ino` in the Arduino IDE.
2. Install required libraries via Library Manager:
   * `Adafruit PWMServoDriver`
   * `Adafruit ADS1X15`
3. Upload to your Arduino Mega 2560.

---

## Quick Start

1. **Connect Hardware:** Plug in your Arduino Mega.
2. **Launch App:**

    ```bash
    python main.py
    ```

3. **Connect Serial:**
    * Go to **Engineer Mode** (Chip Icon).
    * Select your COM port and click **CONNECT**.
    * Click **SCAN I2C** to verify your modules are detected.
4. **Move Robot:**
    * Go to **Pilot View** (Home Icon).
    * Drag a slider on the right panel. The virtual ghost will move.
    * If hardware is powered, the physical robot will sync to the ghost.

---

## Project Structure

* `core/`: Physics engine, Kinematics solver, and Control Loops.
* `ui/`: PyQt6 Widgets, 3D Viewport, and Themes.
* `config/`: JSON definitions for Robots (`inmoov_standard.json`) and Hardware Maps.
* `communication/`: Serial protocols and Telemetry parsers.
* `sourcetruth/`: Definitive wiring guides and schematics.
