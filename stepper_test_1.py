import machine
import utime

STEP_PIN = machine.Pin(16, machine.Pin.OUT)
DIR_PIN = machine.Pin(17, machine.Pin.OUT)
EN_PIN = machine.Pin(18, machine.Pin.OUT)
onboard_led = machine.Pin(25, machine.Pin.OUT)

# Set initial direction and step values
EN_PIN.value(0)
DIR_PIN.value(1)
onboard_led.value(0)

# Define function to step the motor
def step_motor(steps, delay):
    onboard_led.value(1)
    for _ in range(steps):
        STEP_PIN.value(1)
        utime.sleep_us(delay)
        STEP_PIN.value(0)
        utime.sleep_us(delay)
    onboard_led.value(0)

# Example: Rotate the motor 200 steps with a delay of 1000 microseconds between steps
# step_motor(100*(200*5.1818), 500)
step_motor(100*(1600*5.1818), 100)

# Turn off the motor and onboard LED
STEP_PIN.value(0)
onboard_led.value(0)
