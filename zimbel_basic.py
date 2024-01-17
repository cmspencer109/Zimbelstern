from machine import Pin
import time

button = Pin(15, Pin.IN, Pin.PULL_UP)
led = Pin(14, Pin.OUT)

button_state = False
zimbel_state = False
led.value(zimbel_state)

debounce_time = 250

while True:
    if button.value() == 0:  # Button is being pressed
        if not button_state:
            #print("Button pressed")
            button_state = True
            zimbel_state = not zimbel_state
            led.value(zimbel_state)
            
            print("Zimbel On" if zimbel_state else "Zimbel Off")
            
            time.sleep_ms(debounce_time) # Debounce after press
    else:  # Button is not being pressed
        if button_state:
            #print("Button released")
            button_state = False
