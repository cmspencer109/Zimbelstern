import uasyncio as asyncio
import utime as time
import uos
from machine import Pin 


# Initialize pins
midi_uart = machine.UART(0, baudrate=31250, tx=Pin(0), rx=Pin(1))
button = Pin(16, Pin.IN, Pin.PULL_UP)
led = Pin(17, Pin.OUT)

# button name ideas:
# ready, queue, set, mark, prime, pre
button_ready = Pin(18, Pin.IN, Pin.PULL_UP)
led_ready = Pin(19, Pin.OUT)

# Modes
MODE_ZIMBEL = "MODE_ZIMBEL"
MODE_PROGRAM = "MODE_PROGRAM"
mode = MODE_ZIMBEL

button_state = False
button_clock = -1
zimbel_state = False
led.value(zimbel_state)

button_ready_state = False
zimbel_ready = False

BUTTON_HOLD_TIME = 1000 # 3000
BLINK_DURATION = 10000 # 30000 ?

debounce_time = 50 #250

midi_trigger_file = "midi_trigger.txt"
midi_trigger_on = ""
midi_trigger_off = ""
midi_triggers = []

# Setup
# If the file already exists, save the contents to the trigger variables
if midi_trigger_file in uos.listdir():
    with open(midi_trigger_file, "rb") as file:
        midi_trigger_on = file.readline().strip()
        midi_trigger_off = file.readline().strip()
        print('Loaded midi triggers')
        print('midi_trigger_on:', midi_trigger_on)
        print('midi_trigger_off:', midi_trigger_off)


def save_midi_triggers(midi_triggers):
    global midi_trigger_on, midi_trigger_off
    with open(midi_trigger_file, "wb") as file:
        file.write(midi_triggers[0] + b'\n')
        file.write(midi_triggers[1] + b'\n')
        midi_trigger_on = midi_triggers[0]
        midi_trigger_off = midi_triggers[1]
        print('Midi triggers saved')


def zimbel_on():
    global zimbel_state
    zimbel_state = True
    led.value(zimbel_state)
    print('Zimbel on')
    zimbel_ready_off()


def zimbel_off():
    global zimbel_state
    zimbel_state = False
    led.value(zimbel_state)
    print('Zimbel off')
    zimbel_ready_off()


def zimbel_ready_on():
    zimbel_off()
    global zimbel_ready
    zimbel_ready = True
    led_ready.value(zimbel_ready)
    print('Zimbel ready on')


def zimbel_ready_off():
    global zimbel_ready
    zimbel_ready = False
    led_ready.value(zimbel_ready)
    print('Zimbel ready off')


def change_mode(new_mode):
    global mode, midi_triggers
    if mode != new_mode:
        print('Mode changed to', new_mode)
        mode = new_mode
        if mode == MODE_PROGRAM:
            # Perform these actions when entering program mode
            zimbel_off()
            midi_triggers = []


async def blink():
    global mode

    start_time = time.ticks_ms()

    # Loop until duration has been reached or the mode changes of program mode
    while time.ticks_diff(time.ticks_ms(), start_time) < BLINK_DURATION and mode == MODE_PROGRAM:
        led.value(not led.value())
        await asyncio.sleep_ms(200)
    # End loop with led off
    led.value(False)
    
    # Reset mode after completing loop
    change_mode(MODE_ZIMBEL)


async def read_midi_task():
    global mode, midi_trigger_on, midi_trigger_off, midi_triggers, zimbel_ready

    while True:
        if midi_uart.any():
            midi_data = midi_uart.read()
            
            # Handle midi data differently based on current mode
            if mode == MODE_ZIMBEL:
                # Handle midi messages while in zimbel mode
                # i.e. listen for midi trigger
                # Filter out Active Sensing byte
                if midi_data != b'\xfe':
                    print('Midi message:', midi_data)
                if midi_trigger_on in midi_data:
                    zimbel_on()
                elif midi_trigger_off in midi_data:
                    zimbel_off()

                status_byte = list(midi_data)[0]
                # if zimbel ready and note on
                if zimbel_ready and (0x90 <= status_byte <= 0x9F):
                    print(hex(status_byte))
                    zimbel_on()

            elif mode == MODE_PROGRAM:
                # Handle midi messages while in program mode
                # i.e. listen for midi and assign to trigger
                # Filter out Active Sensing byte
                if midi_data != b'\xfe':
                    trimmed_data = midi_data[1:] # Remove status byte from beginning of message
                    midi_triggers.append(trimmed_data)

                    if len(midi_triggers) == 1:
                        print("Assigning to midi_trigger_on:", trimmed_data)

                    if len(midi_triggers) == 2:
                        print("Assigning to midi_trigger_off:", trimmed_data)

                    if len(midi_triggers) >= 2:
                        save_midi_triggers(midi_triggers)
                        change_mode(MODE_ZIMBEL)
        
        # Yield control to event loop
        await asyncio.sleep_ms(10)


async def read_button_task():
    global button_state, button_clock, zimbel_state, mode

    while True:
        if button.value() == 0:  # Button is being pressed
            if not button_state:
                #print('Button pressed')
                button_state = True
                button_clock = time.ticks_ms()
                
                # Toggle zimbel state
                zimbel_off() if zimbel_state else zimbel_on()
                
                # Debounce after press
                await asyncio.sleep_ms(debounce_time)
            
            # Check if the button has been held for x number of ms
            if time.ticks_diff(time.ticks_ms(), button_clock) >= BUTTON_HOLD_TIME:
                change_mode(MODE_PROGRAM)
                await blink()
            
        else:  # Button is not being pressed
            if button_state:
                #print('Button released')
                button_state = False
        
        # Yield control to event loop
        await asyncio.sleep_ms(10)


async def button_ready_task():
    global button_ready_state, zimbel_ready

    while True:
        if button_ready.value() == 0:  # Button is being pressed
            if not button_ready_state:
                # print('READY pressed')
                button_ready_state = True
                
                # Toggle zimbel ready state
                zimbel_ready_off() if zimbel_ready else zimbel_ready_on()

                # Debounce after press
                await asyncio.sleep_ms(debounce_time)
            
        else:  # Button is not being pressed
            if button_ready_state:
                # print('READY released')
                button_ready_state = False
        
        # Yield control to event loop
        await asyncio.sleep_ms(10)


async def main():
    # Create task handlers
    button_task_handler = asyncio.create_task(read_button_task())
    midi_task_handler = asyncio.create_task(read_midi_task())
    button_ready_task_handler = asyncio.create_task(button_ready_task())
    #star_handler = #TODO

    # Run the event loop
    await asyncio.gather(button_task_handler, midi_task_handler, button_ready_task_handler)

# Run the main function to start the event loop
asyncio.run(main())
