/*
The following program is intended for use with the Zimbelstern Star of Martin Luther Church, Sunset Hills, MO.
The program receives on and off communications, as well as speed values via a serial connection.

Bytes should be streamed to the device at minimum more than once per second. If the device does not receive communication 
after 1 second, it will shut off on its own. This is to prevent a runaway uncontrolled process in case of a connection failure.

Bytes are sent in hex form, where the upper nibble should be high (F) to indicate that it should turn on. 
The lower nibble 0 - F maps to the min and max speed constants defined below.

Examples:
0xF0 - Run at the slowest speed
0xF8 - Run at a medium speed
0xFF - Run at the maximum speed
0x00 - Doesn't do anything because the upper nibble is not high

*/

#include <AccelStepper.h>

// Define pins
#define ENABLE_PIN 2
#define DIRECTION_PIN 3
#define STEP_PIN 4

const int MIN_SPEED = 1000;
const int MAX_SPEED = 4000;
const int ACCELERATION = 500;

const int STEPS_IN_ONE_REVOLUTION = 8300; // 1600 steps * 5.187:1 gearbox ratio

unsigned long lastByteReceivedTime = 0;
bool motorRunning = false;

AccelStepper stepper(AccelStepper::DRIVER, STEP_PIN, DIRECTION_PIN);

void setup() {
  // Set the pins
  pinMode(ENABLE_PIN, OUTPUT);
  pinMode(DIRECTION_PIN, OUTPUT);
  pinMode(STEP_PIN, OUTPUT);

  // Set the maximum speed and acceleration
  stepper.setMaxSpeed(MAX_SPEED);
  stepper.setAcceleration(ACCELERATION);

  // Initialize Serial communication
  Serial.begin(9600);
}

void startMotor(int speed) {
  digitalWrite(ENABLE_PIN, LOW); // Low is on
  stepper.setMaxSpeed(speed);
  stepper.move(2147483647); // Set the largest possible position
  stepper.run();
  motorRunning = true;
}

void stopMotor() {
  stepper.stop();
  motorRunning = false;
}

// Stops the motor on the closest quarter revolution with full deceleration
void stopMotorOnQuarter() {
  /* stepper.stop() updates the target position to the point at which it will stop
     based on the current speed and rate at which it will slow down.
     We then add to this number the smallest amount needed to make it divisble by
     the number of steps in a quarter revolution, and move to this new position.
  */
  stepper.stop();
  long targetPosition = stepper.targetPosition();
  int stepsInQuarterRevolution = STEPS_IN_ONE_REVOLUTION / 4;
  long targetPositionToEndOnAQuarter = targetPosition + (stepsInQuarterRevolution - (targetPosition % stepsInQuarterRevolution));
  stepper.moveTo(targetPositionToEndOnAQuarter);
  motorRunning = false;
}

void loop() {
  // Check if data is available on Serial
  if (Serial.available() > 0) {

    byte receivedByte = Serial.read();
    // Serial.println(receivedByte);

    // Extract upper nibble for control and lower nibble for speed
    byte control = (receivedByte & 0xF0) >> 4;
    byte speedValue = receivedByte & 0x0F;

    // Map 0 - F to the min and max speeds so sender can control the speed
    int speed = map(speedValue, 0, 15, MIN_SPEED, MAX_SPEED);

    // Check the upper nibble for control
    if (control == 0x0F) {
      startMotor(speed);
    }
    
    // Update last byte received time
    lastByteReceivedTime = millis();
  }

  // Stop the motor if no bytes received for 1 second
  if (millis() - lastByteReceivedTime > 1000 && motorRunning) {
    // Choose how you want to stop the motor
    // stopMotor();
    stopMotorOnQuarter();
  }

  // Run the stepper motor
  stepper.run();

  // Disable stepper driver when motor is not turning to save power
  if (!stepper.isRunning() && !motorRunning) {
    digitalWrite(ENABLE_PIN, HIGH); // High is off
  }
}
