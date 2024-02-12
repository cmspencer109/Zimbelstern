from machine import Pin
import time

# Define the GPIO pins
dir_pin = Pin(16, Pin.OUT)
step_pin = Pin(17, Pin.OUT)
enable_pin = Pin(18, Pin.OUT)

# Set the initial direction and enable the motor
dir_pin.value(1)  # Set direction (1 or 0 depending on the motor orientation)
enable_pin.value(0)  # Enable the motor

# Function to step the motor
def step_motor(steps, delay):
    for _ in range(steps):
        step_pin.value(1)
        time.sleep_us(delay)
        step_pin.value(0)
        time.sleep_us(delay)

# Number of steps and delay for each step (adjust as needed)
num_steps = 1*5.187*1600
step_delay = 100  # in microseconds

# Rotate the motor
step_motor(num_steps, step_delay)

# Disable the motor
enable_pin.value(1)
