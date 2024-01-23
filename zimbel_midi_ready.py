import uasyncio as asyncio
import utime as time
import uos
from machine import Pin 

#TODO handle ID when organ turns on ?
# note: organ id might reset everytime its turned off/on

# Initialize pins
midi_uart = machine.UART(0, baudrate=31250, tx=Pin(0), rx=Pin(1))
button = Pin(15, Pin.IN, Pin.PULL_UP)
led = Pin(14, Pin.OUT)

# button name ideas:
# ready, queue, set, mark, prime, pre
button_ready = Pin(13, Pin.IN, Pin.PULL_UP)
led_ready = Pin(12, Pin.OUT)

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

DEBOUNCE_TIME = 250 # 50-250 ?
YIELD_TIME = 1 # 0-10?

midi_trigger_filename = 'midi_trigger.txt'
midi_trigger_bytes = []

# Setup
# If the file already exists, save the contents to the trigger variables
if midi_trigger_filename in uos.listdir():
    with open(midi_trigger_filename, "rb") as file:
        midi_trigger_on = file.readline().strip()
        midi_trigger_off = file.readline().strip()
        print('Loaded midi triggers')
        print('midi_trigger_on:', midi_trigger_on)
        print('midi_trigger_off:', midi_trigger_off)


def zimbel_on():
    global zimbel_state
    if not zimbel_state:
        zimbel_state = True
        led.value(zimbel_state)
        print('Zimbel on')
        zimbel_ready_off()


def zimbel_off():
    global zimbel_state
    if zimbel_state:
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
    global mode, midi_trigger_on_off
    if mode != new_mode:
        print('Mode changed to', new_mode)
        mode = new_mode
        if mode == MODE_PROGRAM:
            # Perform these actions when entering program mode
            zimbel_off()
            midi_trigger_on_off = []


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


# Note on helper
def is_note_on(midi_bytes):
    # Check if the list has at least 3 elements
    if len(midi_bytes) < 3:
        return False

    # Check if the status byte indicates a Note On message (status byte starts with '1001' in binary)
    if (midi_bytes[0] & 0xF0) == 0x90:
        # Check if the velocity is greater than 0 (to distinguish Note On from Note Off)
        if midi_bytes[2] > 0:
            return True

    return False


def bits(hex_number, total_width=8):
    binary_representation = bin(hex_number)[2:]
    return '0' * (total_width - len(binary_representation)) + binary_representation


def bytes_match_trigger(input_bytes):
    global midi_trigger_bytes

    print('checking if bytes match trigger')
    print('number of bytes in trigger', len(midi_trigger_bytes))
    print('number of bytes received', len(input_bytes))

    for i in range(len(midi_trigger_bytes)):
        # save time by not checking empty bytes
        if midi_trigger_bytes[i] == 0: continue

        midi_trigger_bits = bits(midi_trigger_bytes[i])
        input_bits = bits(input_bytes[i])

        print('trigger bits', midi_trigger_bits)
        print('input bits', input_bits)

        for j in range(8):
            # not a match if our trigger bit is off when it should be on
            if int(midi_trigger_bits[j]) == 1 and int(input_bits[j]) == 0:
                print('doesnt match trigger, returning false')
                return False
    return True


async def read_midi_task():
    global mode, zimbel_ready, midi_trigger_bytes

    while True:
        if midi_uart.any():
            midi_bytes = list(midi_uart.read())
            
            # Handle midi data differently based on current mode
            if mode == MODE_ZIMBEL:
                # Filter out Active Sensing byte
                if midi_bytes == [0xFE]:
                    continue
                print('Midi message:', midi_bytes)
                
                # Handle midi messages while in zimbel mode
                # i.e. listen for midi trigger
                if midi_bytes[0] == 0xF0: # testing sysex only for now
                    if bytes_match_trigger(midi_bytes[7:-2]):
                        zimbel_on()
                    else: # TODO: READY TO TEST
                        zimbel_off() 

                # if zimbel ready and note on
                if zimbel_ready and is_note_on(midi_bytes):
                    print('zimbel ready and note on')
                    zimbel_on()

            elif mode == MODE_PROGRAM:
                # Handle midi messages while in program mode
                # i.e. listen for midi and assign to trigger
                # Filter out Active Sensing byte
                if midi_bytes != [0xFE]:
                    print('Program mode only working with Rodgers SYSEX right now')
                    # save midi trigger
                    midi_trigger_bytes = midi_bytes[7:-2]
                    print('Saved midi trigger:', midi_trigger_bytes)
                    change_mode(MODE_ZIMBEL)
        
        # Yield control to event loop
        await asyncio.sleep_ms(YIELD_TIME)


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
                await asyncio.sleep_ms(DEBOUNCE_TIME)
            
            # Check if the button has been held for x number of ms
            if time.ticks_diff(time.ticks_ms(), button_clock) >= BUTTON_HOLD_TIME:
                change_mode(MODE_PROGRAM)
                await blink()
            
        else:  # Button is not being pressed
            if button_state:
                #print('Button released')
                button_state = False
        
        # Yield control to event loop
        await asyncio.sleep_ms(YIELD_TIME)


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
                await asyncio.sleep_ms(DEBOUNCE_TIME)
            
        else:  # Button is not being pressed
            if button_ready_state:
                # print('READY released')
                button_ready_state = False
        
        # Yield control to event loop
        await asyncio.sleep_ms(YIELD_TIME)


async def main():
    # Create task handlers
    button_task_handler = asyncio.create_task(read_button_task())
    midi_task_handler = asyncio.create_task(read_midi_task())
    button_ready_task_handler = asyncio.create_task(button_ready_task())
    #star_handler = #TODO ?

    # Run the event loop
    await asyncio.gather(button_task_handler, midi_task_handler, button_ready_task_handler)

# Run the main function to start the event loop
asyncio.run(main())
