# Simple Raspberry Pi Pico program to turn on onboard LED

import machine
import utime

# Define the onboard LED pin
led_pin = machine.Pin(25, machine.Pin.OUT)

# Turn on the onboard LED
led_pin.value(1)

# Wait for a few seconds (you can adjust the duration as needed)
utime.sleep(5)

# Turn off the onboard LED
led_pin.value(0)
