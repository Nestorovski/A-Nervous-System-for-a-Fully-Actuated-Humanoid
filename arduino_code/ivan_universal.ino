#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include <Adafruit_ADS1X15.h>

// =========================================================
//      MODULE DISTRIBUTED FIRMWARE v2.8 (Full Bang-Bang)
// =========================================================

#define MUX_ADDR 0x70  
#define PCA_ADDR 0x40
#define ADS_ADDR 0x48

// PCA9685 Setup
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(PCA_ADDR);
Adafruit_ADS1115 ads;

// Constants
// CHANGED: 60Hz is required for Servos. 
// DC Motors will use Bang-Bang (Full ON) mode to avoid jitter at this frequency.
#define PWM_FREQ 60   
#define NUM_MOTORS 4
#define NUM_POTS 4

// Servo Calibration
#define SERVOMIN  150 // This is the 'minimum' pulse length count (approx 0 deg)
#define SERVOMAX  600 // This is the 'maximum' pulse length count (approx 180 deg)

// Global State
int16_t pot_offsets[NUM_POTS] = {0};
bool pid_enabled = false;
int current_bus = -99; 

void setup() {
  Serial.begin(115200);
  Wire.begin();
  
  // Initialize default bus
  pwm.begin();
  pwm.setOscillatorFrequency(27000000);
  pwm.setPWMFreq(PWM_FREQ);
  
  Serial.println("READY");
}

// ---------------------------------------------------------
//  MULTIPLEXER LOGIC
// ---------------------------------------------------------

void tcaselect(uint8_t i) {
  if (i > 7) return;
  Wire.beginTransmission(MUX_ADDR);
  Wire.write(1 << i);
  Wire.endTransmission();
}

void setBus(int port) {
  if (port == current_bus) return;

  if (port == -1) {
    // Direct Mode
    Wire.beginTransmission(MUX_ADDR);
    Wire.write(0); 
    Wire.endTransmission();
  } else {
    // Mux Mode
    tcaselect(port);
  }
  current_bus = port;
  delay(10);
}

// ---------------------------------------------------------
//  MAIN LOOP
// ---------------------------------------------------------

void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    if (input.length() == 0) return;

    // PROTOCOL: <TARGET_PORT>:<COMMAND>
    int split = input.indexOf(':');
    if (split == -1) return; 

    String portStr = input.substring(0, split);
    String cmdStr = input.substring(split + 1);

    // 1. Handle System Scans
    if (portStr == "SCAN" && cmdStr == "SYSTEM") {
      scanTopology();
      return;
    }

    // 2. Switch Bus
    if (portStr == "D") setBus(-1);
    else setBus(portStr.toInt());

    // 3. Execute Command
    processCommand(cmdStr);
  }
}

void processCommand(String cmd) {
  
  if (cmd == "TEST_POTS") {
    readPots();
  }
  else if (cmd == "SCAN_I2C") {
    scanCurrentBus(); 
  }
  // --- TEST BUTTONS (Engineeer Mode) ---
  else if (cmd.startsWith("TEST_") && cmd.endsWith("_FWD:50")) { // Matches "50" from legacy buttons
    String motor = cmd.substring(5, cmd.indexOf("_FWD"));
    testMotor(motor, true, 100); // FORCE 100 for Bang-Bang
    Serial.println("CMD_OK");
  }
  else if (cmd.startsWith("TEST_") && cmd.endsWith("_REV:50")) {
    String motor = cmd.substring(5, cmd.indexOf("_REV"));
    testMotor(motor, false, 100); // FORCE 100 for Bang-Bang
    Serial.println("CMD_OK");
  }
  else if (cmd.startsWith("TEST_") && (cmd.endsWith("_FWD:0") || cmd.endsWith("_REV:0"))) {
    // Stop Command
    String motor = cmd.substring(5, cmd.lastIndexOf("_"));
    setMotorDuty(motor, 0, true);
    Serial.println("CMD_OK");
  }
  // --- SET COMMANDS (Sliders/IK) ---
  else if (cmd.startsWith("SET_")) {
    int colon = cmd.indexOf(':');
    String device = cmd.substring(4, colon); // "MOTOR1A" or "SERVO1"
    int val = cmd.substring(colon+1).toInt();
    
    // Distinguish between Motor and Servo
    if (device.startsWith("SERVO")) {
      setServoAngle(device, val);
    } else {
      setMotorDuty(device, val, true);
    }
  }
  else if (cmd == "CALIB_POTS") {
    calibratePots();
  }
}

// ---------------------------------------------------------
//  READING
// ---------------------------------------------------------
void readPots() {
  ads.begin(); 
  
  int16_t pots[NUM_POTS];
  for (int i=0; i<NUM_POTS; i++) {
    pots[i] = ads.readADC_SingleEnded(i) - pot_offsets[i]; 
  }
  
  Serial.print("POTS:");
  for (int i=0; i<NUM_POTS; i++) {
    Serial.print(pots[i]);
    if (i < NUM_POTS-1) Serial.print(",");
  }
  Serial.println();
}

void scanCurrentBus() {
  Serial.print("I2C_SCAN:");
  for (byte addr = 1; addr < 127; addr++) {
    if (addr == MUX_ADDR) continue;
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      Serial.print("0x");
      Serial.print(addr, HEX);
      Serial.print(",");
    }
  }
  Serial.println();
}

// ---------------------------------------------------------
//  PIN MAPPING
// ---------------------------------------------------------
void getMotorChannels(String motor, int &pwm_ch, int &in1_ch, int &in2_ch) {
  // MOTOR 1 = TB6612 #1 Output A (Pins 5, 3, 4)
  if (motor == "MOTOR1" || motor == "MOTOR1A") { 
    pwm_ch=5; in1_ch=3; in2_ch=4; 
  }
  // MOTOR 2 = TB6612 #1 Output B (Pins 0, 1, 2)
  else if (motor == "MOTOR2" || motor == "MOTOR1B") { 
    pwm_ch=0; in1_ch=1; in2_ch=2; 
  } 
  // MOTOR 3 = TB6612 #2 Output A (Pins 8, 10, 9)
  else if (motor == "MOTOR3" || motor == "MOTOR2A") { 
    pwm_ch=8; in1_ch=10; in2_ch=9; 
  }
  // MOTOR 4 = TB6612 #2 Output B (Pins 13, 11, 12)
  else if (motor == "MOTOR4" || motor == "MOTOR2B") { 
    pwm_ch=13; in1_ch=11; in2_ch=12; 
  } 
}

void testMotor(String motor, bool fwd, int pct) {
  setMotorDuty(motor, pct, fwd);
  delay(1000); 
  setMotorDuty(motor, 0, fwd);
}

// MODIFIED FOR BANG-BANG CONTROL (NO JITTER)
void setMotorDuty(String motor, int pct, bool fwd) {
  int pwm_ch, in1_ch, in2_ch;
  getMotorChannels(motor, pwm_ch, in1_ch, in2_ch);
  
  if (pct == 0) {
    // HARD STOP
    pwm.setPin(pwm_ch, 0, false); // Turn Enable Pin OFF
    pwm.setPin(in1_ch, 0, false);
    pwm.setPin(in2_ch, 0, false);
  } else {
    // FULL ON (Ignore exact percentage, go 100%)
    // This prevents the 60Hz Flicker/Vibration
    
    // Set Enable Pin to Logic HIGH (4096 ON, 0 OFF)
    pwm.setPin(pwm_ch, 4096, false); 
    
    if (fwd) { 
      pwm.setPin(in1_ch, 4096, false); // Logic HIGH
      pwm.setPin(in2_ch, 0, false);    // Logic LOW
    }
    else { 
      pwm.setPin(in1_ch, 0, false);    // Logic LOW
      pwm.setPin(in2_ch, 4096, false); // Logic HIGH
    }
  }
}

// NEW SERVO FUNCTION
void setServoAngle(String servoName, int angle) {
  int pin = -1;
  // Standard IvanModule Pinout
  if (servoName == "SERVO1") pin = 6;
  else if (servoName == "SERVO2") pin = 7;
  else if (servoName == "SERVO3") pin = 14;
  else if (servoName == "SERVO4") pin = 15;
  
  if (pin != -1) {
    // Safety Constrain
    if (angle < 0) angle = 0;
    if (angle > 180) angle = 180;
    
    // Map Angle to Pulse Width
    int pulse = map(angle, 0, 180, SERVOMIN, SERVOMAX);
    pwm.setPWM(pin, 0, pulse);
  }
}

void calibratePots() {
  ads.begin(); 
  for (int i=0; i<NUM_POTS; i++) {
    pot_offsets[i] = ads.readADC_SingleEnded(i);
  }
  Serial.println("CALIB_DONE");
}

// ---------------------------------------------------------
//  TOPOLOGY SCANNER
// ---------------------------------------------------------
void scanTopology() {
  Serial.println("TOPOLOGY_START");
  
  // 1. Check Direct Bus
  setBus(-1);
  if (checkDevice(PCA_ADDR)) Serial.println("FOUND:Direct (No Mux)");

  // 2. Check Mux Ports 0-7
  for (int i=0; i<8; i++) {
    setBus(i);
    // Double check delay to let Mux settle
    delay(5);
    if (checkDevice(PCA_ADDR)) {
      Serial.print("FOUND:Port ");
      Serial.println(i);
    }
  }
  Serial.println("TOPOLOGY_END");
}

bool checkDevice(uint8_t addr) {
  Wire.beginTransmission(addr);
  return (Wire.endTransmission() == 0);
}