import machine
import time

# Set GPIO pins
mosfet_pin = 16
onboard_led_pin = 25  # Onboard LED pin for Raspberry Pi Pico

# Configure GPIO pins as outputs
mosfet = machine.Pin(mosfet_pin, machine.Pin.OUT)
onboard_led = machine.Pin(onboard_led_pin, machine.Pin.OUT)

# Function to pulse the electromagnet and flash the onboard LED
def pulse_and_flash():
    # Turn on the electromagnet
    mosfet.on()
    # Flash the onboard LED
    onboard_led.on()
    
    time.sleep_ms(1000)  # Adjust the pulse duration as needed
    
    # Turn off both the electromagnet and the onboard LED
    mosfet.off()
    onboard_led.off()

# Main loop
while True:
    pulse_and_flash()
    time.sleep(1)  # Wait for one second before the next pulse
