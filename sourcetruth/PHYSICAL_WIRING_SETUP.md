# InMoov - PHYSICAL WIRING SETUP

---

## EXECUTIVE SUMMARY

This document defines the **physical wiring assignments** for the InMoov distributed system. Each IvanModule can support up to **4 N20 DC motors** + **4 SG90 servos** simultaneously. Actuators are distributed across modules to balance load and enable easy wire extension.

**Wiring Philosophy:**

- **4 motors maximum per module** (hardware limitation)
- **4 servos maximum per module** (practical limit)
- **4 potentiometers per module** (ADS1115 ADC channels for N20 motor feedback)
- **Wire extension allowed** - motors/servos can be physically distant from modules
- **Load balancing** - distribute actuators across available modules
- **Face servos only** - all facial expressions use SG90 servos
- **Potentiometer mapping** - Each N20 DC motor requires a potentiometer connected to ADS1115 A0-A3

---

## MODULE DISTRIBUTION PLAN

### **Available IvanModules**

- **Port 0**: Head/Neck motors + Face servos
- **Port 1**: Left Arm motors + Face servos
- **Port 2**: Right Arm motors + Face servos
- **Port 3**: Torso motors + Face servos
- **Port 4**: Right Hand motors + Face servos
- **Port 5**: Left Hand motors + Face servos
- **Port 6**: Face servos only
- **Port 7**: Spare/Expansion

### **Actuator Distribution Logic**

- **27 N20 motors** → 7 modules (28 slots, 27 used + 1 spare)
- **15 SG90 face servos** → Distributed across modules (32 servo slots available)
- **Each module can have BOTH motors AND servos simultaneously**

---

## ACTUATOR-TO-MODULE MAPPING

### **PORT 0: HEAD/NECK MODULE**

**Location:** Head area
**Motors:** 4/4 used
**Servos:** 3/4 used

| ID | Name | Type | PCA Pin | ADS Ch | Motor/Servo Name | Notes |
|----|------|------|---------|--------|------------------|-------|
| 1 | Neck Piston Left | N20 | 5 | 0 | MOTOR1A | Front neck |
| 2 | Neck Main Tilt | N20 | 0 | 1 | MOTOR1B | Main head tilt |
| 3 | Neck Piston Right | N20 | 8 | 2 | MOTOR2A | Front neck |
| 26 | Head Rotation | N20 | 13 | 3 | MOTOR2B | Head yaw |
| 27 | Left Eyebrow | SG90 | 6 | - | SERVO1 | Eye mechanism |
| 28 | Right Eyebrow | SG90 | 7 | - | SERVO2 | Eye mechanism |
| 29 | Left Eyelid | SG90 | 14 | - | SERVO3 | Eye mechanism |

### **PORT 1: LEFT ARM MODULE**

**Location:** Left shoulder area
**Motors:** 4/4 used
**Servos:** 2/4 used

| ID | Name | Type | PCA Pin | ADS Ch | Motor/Servo Name | Notes |
|----|------|------|---------|--------|------------------|-------|
| 4 | Shoulder Pitch | N20 | 5 | 0 | MOTOR1A | Shoulder up/down |
| 5 | Shoulder Roll | N20 | 0 | 1 | MOTOR1B | Shoulder twist |
| 6 | Bicep Flexion | N20 | 8 | 2 | MOTOR2A | Elbow bend |
| 7 | Bicep Rotate | N20 | 13 | 3 | MOTOR2B | Forearm twist |
| 30 | Right Eyelid | SG90 | 6 | - | SERVO1 | Eye mechanism |
| 31 | Eyes X (Side) | SG90 | 7 | - | SERVO2 | Eye tracking |

### **PORT 2: RIGHT ARM MODULE**

**Location:** Right shoulder area
**Motors:** 4/4 used
**Servos:** 2/4 used

| ID | Name | Type | PCA Pin | ADS Ch | Motor/Servo Name | Notes |
|----|------|------|------|--------|------------------|-------|
| 8 | Shoulder Pitch | N20 | 5 | 0 | MOTOR1A | Shoulder up/down |
| 9 | Shoulder Roll | N20 | 0 | 1 | MOTOR1B | Shoulder twist |
| 10 | Bicep Flexion | N20 | 8 | 2 | MOTOR2A | Elbow bend |
| 11 | Bicep Rotate | N20 | 13 | 3 | MOTOR2B | Forearm twist |
| 32 | Eyes Y (Up) | SG90 | 6 | - | SERVO1 | Eye tracking |
| 33 | Left Lip | SG90 | 7 | - | SERVO2 | Mouth mechanism |

### **PORT 3: TORSO MODULE**

**Location:** Torso area
**Motors:** 3/4 used
**Servos:** 2/4 used

| ID | Name | Type | PCA Pin | ADS Ch | Motor/Servo Name | Notes |
|----|------|------|---------|--------|------------------|-------|
| 23 | Left Pinky | N20 | 8 | 2 | MOTOR2A | Left pinky |
| 24 | Torso Rotation | N20 | 5 | 0 | MOTOR1A | Body twist |
| 25 | Torso Lateral | N20 | 0 | 1 | MOTOR1B | Body lean |
| 34 | Right Cheek | SG90 | 6 | - | SERVO1 | Facial expression |
| 35 | Nose | SG90 | 7 | - | SERVO2 | Facial expression |

### **PORT 4: RIGHT HAND MODULE**

**Location:** Right forearm/wrist area
**Motors:** 4/4 used
**Servos:** 2/4 used

| ID | Name | Type | PCA Pin | ADS Ch | Motor/Servo Name | Notes |
|----|------|------|---------|--------|------------------|-------|
| 13 | Thumb | N20 | 5 | 0 | MOTOR1A | Thumb flexion |
| 14 | Index | N20 | 0 | 1 | MOTOR1B | Index flexion |
| 15 | Middle | N20 | 8 | 2 | MOTOR2A | Middle flexion |
| 16 | Ring | N20 | 13 | 3 | MOTOR2B | Ring flexion |
| 36 | Mouth Width | SG90 | 6 | - | SERVO1 | Jaw width |
| 37 | Mouth Height | SG90 | 7 | - | SERVO2 | Jaw height |

### **PORT 5: LEFT HAND MODULE**

**Location:** Left forearm/wrist area
**Motors:** 4/4 used
**Servos:** 2/4 used

| ID | Name | Type | PCA Pin | ADS Ch | Motor/Servo Name | Notes |
|----|------|------|---------|--------|------------------|-------|
| 19 | Thumb | N20 | 5 | 0 | MOTOR1A | Thumb flexion |
| 20 | Index | N20 | 0 | 1 | MOTOR1B | Index flexion |
| 21 | Middle | N20 | 8 | 2 | MOTOR2A | Middle flexion |
| 22 | Ring | N20 | 13 | 3 | MOTOR2B | Ring flexion |
| 38 | Left Cheek | SG90 | 6 | - | SERVO1 | Facial expression |
| 39 | Forehead | SG90 | 7 | - | SERVO2 | Forehead wrinkles |

### **PORT 6: MIXED MODULE (WRISTS + JAW)**

**Location:** Face/wrist area
**Motors:** 4/4 used
**Servos:** 2/4 used

| ID | Name | Type | PCA Pin | ADS Ch | Motor/Servo Name | Notes |
|----|------|------|---------|--------|------------------|-------|
| 12 | Right Wrist Rotate | N20 | 5 | 0 | MOTOR1A | Right wrist |
| 17 | Right Pinky | N20 | 0 | 1 | MOTOR1B | Right pinky |
| 18 | Left Wrist Rotate | N20 | 8 | 2 | MOTOR2A | Left wrist |
| 42 | Jaw Mechanism | N20 | 13 | 3 | MOTOR2B | Jaw motor |
| 40 | Neck Roll | SG90 | 6 | - | SERVO1 | Neck movement |
| 41 | Chin Mechanism | SG90 | 7 | - | SERVO2 | Chin control |

### **PORT 7: SPARE/EXPANSION**

**Location:** Reserved
**Motors:** 0/4 available
**Servos:** 0/4 available

*No actuators assigned - available for future expansion

---

## PIN MAPPING REFERENCE

### **IvanModule PCA9685 Pin Usage**

```s
Pin 0:  MOTOR1B PWM (speed)
Pin 1:  MOTOR1B DIR2 (direction)
Pin 2:  MOTOR1B DIR1 (direction)
Pin 3:  MOTOR1A DIR1 (direction)
Pin 4:  MOTOR1A DIR2 (direction)
Pin 5:  MOTOR1A PWM (speed)
Pin 6:  SERVO1 PWM (signal)
Pin 7:  SERVO2 PWM (signal)
Pin 8:  MOTOR2A PWM (speed)
Pin 9:  MOTOR2A DIR2 (direction)
Pin 10: MOTOR2A DIR1 (direction)
Pin 11: MOTOR2B DIR1 (direction)
Pin 12: MOTOR2B DIR2 (direction)
Pin 13: MOTOR2B PWM (speed)
Pin 14: SERVO3 PWM (signal)
Pin 15: SERVO4 PWM (signal)
```

### **IvanModule ADS1115 Channel Usage**

```s
A0: MOTOR1A potentiometer feedback
A1: MOTOR1B potentiometer feedback
A2: MOTOR2A potentiometer feedback
A3: MOTOR2B potentiometer feedback
```

---

## POWER DISTRIBUTION

### **Per IvanModule Power Requirements**

- **Logic Power**: 5V, 100mA (Arduino regulated)
- **Motor Power**: 6-12V, 500mA per motor (external supply)
- **Servo Power**: 5V, 100mA per servo (Arduino or external)

### **Total System Power**

- **Motors**: 27 × 200mA = ~5.4A at 12V
- **Servos**: 15 × 100mA = ~1.5A at 5V
- **Logic**: 8 × 100mA = ~0.8A at 5V
- **Total**: ~7.7A (use 10A supply minimum)

---

## TESTING & VALIDATION

### **Module Testing Order**

1. **Port 0**: Test head/neck motors first
2. **Port 1-2**: Test arms (critical for balance)
3. **Port 3**: Test torso
4. **Port 4-5**: Test hands
5. **Port 6-7**: Test face servos last

### **Wire Extension Guidelines**

- **Motor wires**: Up to 2m extension allowed
- **Servo wires**: Up to 1m extension allowed
- **Feedback potentiometers**: Keep close to module (<50cm)
- **Use shielded cable** for servo signals if >50cm

---

## CONFIGURATION WORKFLOW

### **Step 1: Physical Assembly**

1. Mount IvanModules in designated locations
2. Connect I2C bus (TCA9548A multiplexer)
3. Wire motors/servos according to this mapping
4. Connect potentiometer feedback
5. Verify power distribution

### **Step 2: Firmware Upload**

1. Upload `ivan_universal.ino` to Arduino Mega
2. Verify I2C addresses (0x40 PCA, 0x48 ADS per module)
3. Test `SCAN:SYSTEM` command

### **Step 3: Software Configuration**

1. Update `map_default.json` with these mappings
2. Test individual actuators
3. Calibrate potentiometer ranges
4. Validate pose commands

---

## CRITICAL NOTES

### **Hardware Limitations**

- **Maximum 4 motors per module** (TB6612FNG limitation)
- **Maximum 4 servos per module** (practical PCA9685 limit)
- **ADS1115 only 4 channels** (one per motor)
- **I2C bus loading** (keep modules <1m from multiplexer)

### **Wire Management**

- **Color coding**: Red(+), Black(GND), White(Signal), Green(Feedback)
- **Strain relief**: All connections must be mechanically secured
- **EMI shielding**: Motor wires away from signal lines
- **Connector standardization**: JST-XH or similar throughout

### **Expansion**

- **Ports 6-7 available** for additional functionality
- **Module daisy-chaining** possible if needed
- **Power distribution** must scale with additional modules

---
