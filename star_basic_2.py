from machine import Pin
import time
import math

GEAR_RATIO = 5.187
STEPS_IN_REVOLUTION = 1600 * GEAR_RATIO

# Define the GPIO pins
dir_pin = Pin(16, Pin.OUT)
step_pin = Pin(17, Pin.OUT)
enable_pin = Pin(18, Pin.OUT)

dir_pin.value(1) # clockwise
enable_pin.value(0) # enable

def easeInSine(start, end, steps):
    result = []
    for i in range(steps):
        t = i / (steps - 1)
        result.append(int(start + (end - start) * (-math.cos(t * math.pi / 2) + 1)))
    return result

def easeInQuad(start, end, steps):
    result = []
    for i in range(steps):
        t = i / (steps - 1)
        result.append(int(start + (end - start) * t**2))
    return result

def easeInCubic(start, end, steps):
    result = []
    for i in range(steps):
        t = i / (steps - 1)
        result.append(int(start + (end - start) * t**3))
    return result

def easeOutSine(start, end, steps):
    result = []
    for i in range(steps):
        t = i / (steps - 1)
        result.append(int(start + (end - start) * math.sin(t * math.pi / 2)))
    return result

def easeOutQuad(start, end, steps):
    result = []
    for i in range(steps):
        t = i / (steps - 1)
        result.append(int(start + (end - start) * (1 - (1 - t)**2)))
    return result

def easeOutCubic(start, end, steps):
    result = []
    for i in range(steps):
        t = i / (steps - 1)
        result.append(int(start + (end - start) * (1 - (1 - t)**3)))
    return result

def log_curve(start, end, num_points):
    # Ensure start is greater than end
    if start <= end:
        raise ValueError("Start value must be greater than end value")

    # Calculate the scaling factor
    scale_factor = (end - start) / math.log10(1 + num_points)

    # Generate the logarithmic curve points
    points = [int(start + scale_factor * math.log10(1 + i)) for i in range(num_points)]

    return points

def step_motor(revolutions, values):
    global step_pin, STEPS_IN_REVOLUTION
    steps = revolutions * STEPS_IN_REVOLUTION

    ratio = steps/len(values)

    for i in range(steps):
        sleep_value = values[int(i/ratio)]
        # sleep_value = values[0]
        # print(sleep_value)
        step_pin.value(1)
        time.sleep_us(sleep_value)
        step_pin.value(0)
        time.sleep_us(sleep_value)

target_delay = 100

# print(log_curve(750, target_delay, 100))

# step_motor(0.25, easeOutSine(750, 200, 25))
# step_motor(0.5, easeOutSine(200, target_delay, 50))
# step_motor(0.75, log_curve(750, target_delay, 100))
# step_motor(2, [target_delay])
step_motor(0.75, log_curve(target_delay, 1500, 100))
# step_motor(1, log_curve(target_delay, 1500, 100))
# step_motor(1.5, easeInCubic(target_delay, 400, 50))
# step_motor(0.25, easeInCubic(400, 4000, 50))

enable_pin.value(1) # disable


# print(easeOutSine(750, 200, 25))
# print(easeOutSine(200, target_delay, 50))