import machine
import time

# Set GPIO pins
ztx851_base_pin = 16
onboard_led_pin = 25  # Onboard LED pin for Raspberry Pi Pico
potentiometer_pin = 27  # Analog pin for the first potentiometer
speed_pot_pin = 26  # Analog pin for the second potentiometer controlling speed

# Configure GPIO pins as outputs
ztx851_base = machine.Pin(ztx851_base_pin, machine.Pin.OUT)
onboard_led = machine.Pin(onboard_led_pin, machine.Pin.OUT)

# Configure the first potentiometer pin as an ADC (Analog to Digital Converter) pin
potentiometer = machine.ADC(potentiometer_pin)

# Configure the second potentiometer pin as an ADC pin
speed_pot = machine.ADC(speed_pot_pin)

# Function to read the first potentiometer value and adjust the pulse duration
def get_pulse_duration():
    # Read the first potentiometer value (0 to 65535)
    pot_value = potentiometer.read_u16()
    
    # Reverse the mapping for pulse duration (e.g., 100 to 10 ms)
    pulse_duration = int(((65535 - pot_value) / 65535) * 90) + 10
    
    return pulse_duration

# Function to read the second potentiometer value and adjust the sleep duration
def get_sleep_duration():
    # Read the second potentiometer value (0 to 65535)
    speed_pot_value = speed_pot.read_u16()
    
    # Keep the mapping as it is for sleep duration (e.g., 1000 to 100 ms)
    sleep_duration = int((speed_pot_value / 65535) * 900) + 100
    
    return sleep_duration

# Function to pulse the electromagnet and flash the onboard LED
def pulse_and_flash():
    # Turn on the electromagnet
    ztx851_base.on()
    # Flash the onboard LED
    onboard_led.on()
    
    pulse_duration = get_pulse_duration()

    print(f'Pulse {pulse_duration} ms')
    
    time.sleep_ms(pulse_duration)  # Adjust the pulse duration based on the first potentiometer
    
    # Turn off both the electromagnet and the onboard LED
    ztx851_base.off()
    onboard_led.off()

# Main loop
while True:
    pulse_and_flash()
    sleep_duration = get_sleep_duration()
    print('Sleeping for:', sleep_duration)
    time.sleep_ms(sleep_duration)  # Adjust the sleep duration based on the second potentiometer
