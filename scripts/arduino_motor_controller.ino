#include <PID_v1.h>

// L298N H-Bridge Connection PINs
#define L298N_enA 9  // PWM Right Motor
#define L298N_enB 11  // PWM Left Motor
#define L298N_in4 8  // Dir Motor B (Left)
#define L298N_in3 7  // Dir Motor B (Left)
#define L298N_in2 13  // Dir Motor A (Right)
#define L298N_in1 12  // Dir Motor A (Right)

// Wheel Encoders Connection PINs
#define right_encoder_phaseA 3  // Interrupt 
#define right_encoder_phaseB 5  
#define left_encoder_phaseA 2   // Interrupt
#define left_encoder_phaseB 4

// Robot parameters
const float WHEEL_RADIUS = 0.033;  // meters
const float WHEEL_SEPARATION = 0.175; // meters
const int ENCODER_PPR = 656; // Pulses per revolution
const float WHEEL_CIRCUMFERENCE = 2 * PI * WHEEL_RADIUS;
const float DISTANCE_PER_PULSE = WHEEL_CIRCUMFERENCE / ENCODER_PPR;

// Encoders
volatile long right_encoder_count = 0;
volatile long left_encoder_count = 0;
long prev_right_count = 0;
long prev_left_count = 0;
unsigned long last_time = 0;
const unsigned long control_interval = 50; // 20Hz control loop

// Command velocities from ROS2 (wheel velocities directly)
double right_wheel_cmd_vel = 0.0;  // rad/s
double left_wheel_cmd_vel = 0.0;   // rad/s

// Measured velocities
double right_wheel_meas_vel = 0.0;  // rad/s
double left_wheel_meas_vel = 0.0;   // rad/s

// PID outputs
double right_motor_cmd = 0.0;  // PWM 0-255
double left_motor_cmd = 0.0;   // PWM 0-255

// PID Controllers
double Kp_r = 15.0, Ki_r = 5.0, Kd_r = 0.1;
double Kp_l = 15.0, Ki_l = 5.0, Kd_l = 0.1;
PID rightPID(&right_wheel_meas_vel, &right_motor_cmd, &right_wheel_cmd_vel, Kp_r, Ki_r, Kd_r, DIRECT);
PID leftPID(&left_wheel_meas_vel, &left_motor_cmd, &left_wheel_cmd_vel, Kp_l, Ki_l, Kd_l, DIRECT);

// Communication
String inputString = "";
bool stringComplete = false;
unsigned long last_cmd_time = 0;
const unsigned long cmd_timeout = 1000; // 1 second timeout

void setup() {
  // Initialize motor pins
  pinMode(L298N_enA, OUTPUT);
  pinMode(L298N_enB, OUTPUT);
  pinMode(L298N_in1, OUTPUT);
  pinMode(L298N_in2, OUTPUT);
  pinMode(L298N_in3, OUTPUT);
  pinMode(L298N_in4, OUTPUT);

  // Initialize encoders
  pinMode(right_encoder_phaseA, INPUT_PULLUP);
  pinMode(right_encoder_phaseB, INPUT_PULLUP);
  pinMode(left_encoder_phaseA, INPUT_PULLUP);
  pinMode(left_encoder_phaseB, INPUT_PULLUP);

  // Attach interrupts
  attachInterrupt(digitalPinToInterrupt(right_encoder_phaseA), rightEncoderISR, CHANGE);
  attachInterrupt(digitalPinToInterrupt(left_encoder_phaseA), leftEncoderISR, CHANGE);

  // Initialize PID
  rightPID.SetMode(AUTOMATIC);
  leftPID.SetMode(AUTOMATIC);
  rightPID.SetOutputLimits(-255, 255);
  leftPID.SetOutputLimits(-255, 255);

  // Initialize serial
  Serial.begin(115200);
  Serial.println("Arduino Motor Controller Ready");
  
  last_time = millis();
}

void loop() {
  unsigned long current_time = millis();
  
  // Read commands from ROS2
  readSerialCommands();
  
  // Safety: Stop if no commands received
  if (current_time - last_cmd_time > cmd_timeout) {
    right_wheel_cmd_vel = 0.0;
    left_wheel_cmd_vel = 0.0;
  }
  
  // Control loop at fixed interval
  if (current_time - last_time >= control_interval) {
    // Calculate wheel velocities from encoders
    calculateWheelVelocities(current_time - last_time);
    
    // Run PID controllers
    rightPID.Compute();
    leftPID.Compute();
    
    // Apply motor commands
    setMotorSpeeds();
    
    // Send feedback to ROS2
    sendFeedback();
    
    last_time = current_time;
  }
}

void readSerialCommands() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    if (inChar == '\n') {
      stringComplete = true;
      break;
    }
    inputString += inChar;
  }
  
  if (stringComplete) {
    parseCommand(inputString);
    inputString = "";
    stringComplete = false;
    last_cmd_time = millis();
  }
}

void parseCommand(String command) {
  // Expected format: "right_wheel_vel,left_wheel_vel"
  // Example: "2.5,-1.8" means right wheel at 2.5 rad/s, left wheel at -1.8 rad/s
  int commaIndex = command.indexOf(',');
  if (commaIndex > 0) {
    right_wheel_cmd_vel = command.substring(0, commaIndex).toFloat();
    left_wheel_cmd_vel = command.substring(commaIndex + 1).toFloat();
  }
}

// Function removed - wheel velocities now come directly from ROS2

void calculateWheelVelocities(unsigned long dt) {
  // Calculate encoder differences
  long right_diff = right_encoder_count - prev_right_count;
  long left_diff = left_encoder_count - prev_left_count;
  
  // Convert to angular velocity (rad/s)
  double dt_sec = dt / 1000.0;
  right_wheel_meas_vel = (right_diff * 2.0 * PI) / (ENCODER_PPR * GEAR_RATIO * dt_sec);
  left_wheel_meas_vel = (left_diff * 2.0 * PI) / (ENCODER_PPR * GEAR_RATIO * dt_sec);
  
  // Update previous counts
  prev_right_count = right_encoder_count;
  prev_left_count = left_encoder_count;
}

void setMotorSpeeds() {
  // Right motor
  if (right_motor_cmd >= 0) {
    digitalWrite(L298N_in1, HIGH);
    digitalWrite(L298N_in2, LOW);
    analogWrite(L298N_enA, constrain(abs(right_motor_cmd), 0, 255));
  } else {
    digitalWrite(L298N_in1, LOW);
    digitalWrite(L298N_in2, HIGH);
    analogWrite(L298N_enA, constrain(abs(right_motor_cmd), 0, 255));
  }
  
  // Left motor
  if (left_motor_cmd >= 0) {
    digitalWrite(L298N_in3, HIGH);
    digitalWrite(L298N_in4, LOW);
    analogWrite(L298N_enB, constrain(abs(left_motor_cmd), 0, 255));
  } else {
    digitalWrite(L298N_in3, LOW);
    digitalWrite(L298N_in4, HIGH);
    analogWrite(L298N_enB, constrain(abs(left_motor_cmd), 0, 255));
  }
}

void sendFeedback() {
  // Send wheel velocities back to ROS2
  // Format: "right_vel,left_vel"
  Serial.print(right_wheel_meas_vel, 4);
  Serial.print(",");
  Serial.println(left_wheel_meas_vel, 4);
}

// Encoder interrupt service routines
void rightEncoderISR() {
  if (digitalRead(right_encoder_phaseA) == digitalRead(right_encoder_phaseB)) {
    right_encoder_count++;
  } else {
    right_encoder_count--;
  }
}

void leftEncoderISR() {
  if (digitalRead(left_encoder_phaseA) == digitalRead(left_encoder_phaseB)) {
    left_encoder_count--;  // Reverse for left wheel
  } else {
    left_encoder_count++;
  }
}
