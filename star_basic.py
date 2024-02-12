from machine import Pin
import time
import math

GEAR_RATIO = 5.187 # Officially 5.18:1
STEPS_IN_REVOLUTION = int(1600 * GEAR_RATIO)

# Define GPIO pins
dir_pin = Pin(16, Pin.OUT)
step_pin = Pin(17, Pin.OUT)
enable_pin = Pin(18, Pin.OUT)

dir_pin.value(1) # Clockwise
enable_pin.value(0) # Enable


def log_curve(start, end, num_points):
    # Ensure start is greater than end
    if start <= end:
        raise ValueError("Start value must be greater than end value")
    # Calculate the scaling factor
    scale_factor = (end - start) / math.log10(1 + num_points)
    # Generate the logarithmic curve points
    points = [int(start + scale_factor * math.log10(1 + i)) for i in range(num_points)]
    return points


def accel_motor(values):
    global scale_factor
    for value in values:
        for _ in range(scale_factor):
            step_pin.value(1)
            time.sleep_us(value)
            step_pin.value(0)
            time.sleep_us(value)


def step_motor(delay, revs):
    global STEPS_IN_REVOLUTION
    steps = revs * STEPS_IN_REVOLUTION
    for _ in range(steps):
        step_pin.value(1)
        time.sleep_us(delay)
        step_pin.value(0)
        time.sleep_us(delay)


start_delay = 750
target_delay = 100
end_delay = 1500
scale_factor = 10
num_points = int(STEPS_IN_REVOLUTION/scale_factor)

acceleration_profile = log_curve(start_delay, target_delay, num_points)
deceleration_profile = log_curve(end_delay, target_delay, num_points)[::-1]

accel_motor(acceleration_profile)
step_motor(target_delay, revs=1)
accel_motor(deceleration_profile)

# motor_on = True
# delay = start_delay

# while motor_on:


enable_pin.value(1) # disable
