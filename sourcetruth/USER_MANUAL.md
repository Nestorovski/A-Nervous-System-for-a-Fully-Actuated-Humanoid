
# Robot Studio - User Manual

## Overview

Robot Studio is the central nervous system for your distributed robot. It bridges kinematic control (Inverse Kinematics, 3D Visualization) with low-level hardware management (Serial communication, I2C Bus scanning, N20/Servo control).

The software is divided into four primary **Modes**, accessible via the left sidebar.

---

## 1. Pilot Mode (Home)

The central command deck for operating the robot.

### The 3D Viewport

* **Cyan Ghost:** Represents the *Target* state (where you want the robot to be).
* **Solid/Bone Model:** Represents the *Physical* state (read from sensors).
* **Navigation:**
  * **Rotate:** Left-Click + Drag
  * **Pan:** Right-Click + Drag
  * **Zoom:** Scroll Wheel

### The Inspector (Right Panel)

* **Sliders:** Direct control over every joint.
* **Values:** Shows the current angle (0-180°). Dragging a slider updates the Ghost immediately.

---

## 2. Engineer Mode (Chip Icon)

This is the hardware configuration suite. Use this to set up your specific wiring topology (e.g., Left Pinky on Port 3, Right Pinky on Port 6).

### Tab 1: Pin Mapping Editor

This table maps a logical Body Part to a physical Pin.

* **ID:** The internal ID of the joint.
* **Mux Port:** Which channel on the TCA9548A (0-7).
* **PCA Pin:** Which pin on the PWM driver (0-15).
* **Motor Type:** `n20` (DC Motor) or `sg90` (Servo).
* **ADS Channel:** The analog pin (0-3) for N20 feedback.
* *Action:* Double-click any cell to edit. Click **Save** to write changes to `config/hardware/map_default.json`.

### Tab 2: System Diagnostic

* **Connect:** Select your Arduino COM port and click Connect.
* **Scan I2C:** Detects connected modules. You should see addresses `0x40` (PCA), `0x48` (ADS), and `0x70` (Mux).
* **Start Live Stream:** Streams real-time potentiometer data from the robot. Green text indicates live updates.
* **Quick Motor Test:** Buttons to pulse specific motors Forward/Reverse for verification.

---

## 3. Advanced Tools

### Architect Mode (Inside Inspector)

Turns the software into a visualizer.

* Select a part in the hierarchy tree.
* Modify properties like **Bone Length**, **Joint Origin**, or **Limits** in real-time.
* Save changes to `config/robots/inmoov_standard.json`.

### Animation Sequencer (Film Icon)

Create movements without code.

1. **Record:** Saves the current pose of the Ghost as a keyframe.
2. **Play:** Smoothly interpolates between recorded frames using cosine easing.
3. **Save/Load:** Export your animations to JSON files.

### Inverse Kinematics (IK)

Found in the **Tools** menu.

* Select an end-effector (e.g., `r_hand_palm`).
* Input target X, Y, Z coordinates (in millimeters).
* Click **Solve & Move** to automatically calculate the joint angles.

---

## Settings & Safety Prototype Version

Located in **Settings Mode (Gear Icon)**:

* **Collision Prevention:** Prevents the Ghost model from entering self-colliding positions.
* **Motor Max Speed:** Effectively always 100%.
* **Tolerance:** The "Deadband" for position seeking. Increase this if motors are jittering or oscillating around the target.

---

## Troubleshooting

**Q: The Ghost moves, but the robot doesn't.**
A:

1. Check **Engineer Mode**. Is the COM port connected?
2. Is the **Motor Max Speed** in Settings > 0?
3. Verify your 12V motor power supply is active (USB power is not enough for motors).

**Q: Motors are moving in the wrong direction.**
A: Swap the motor wires at the TB6612FNG terminal, or reverse the min/max limits in Architect Mode.

**Q: I2C Scan only finds 0x70.**
A: The Multiplexer is working, but the IvanModules are not. Check the SDA/SCL wiring between the Multiplexer and the Modules.
