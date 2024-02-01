import machine
import uasyncio
import utime
import uos
from machine import Pin

# TODO: handle ID when organ turns on ?
# organ id might reset every time its turned off/on

# Initialize pins
midi_uart = machine.UART(0, baudrate=31250, tx=Pin(0), rx=Pin(1))

prepare_button = Pin(13, Pin.IN, Pin.PULL_UP)
prepare_button_light = Pin(12, Pin.OUT)
prepare_button_state = False

zimbel_button = Pin(15, Pin.IN, Pin.PULL_UP)
zimbel_button_light = Pin(14, Pin.OUT)
zimbel_button_state = False

# Modes
MODE_ZIMBEL = "MODE_ZIMBEL"
MODE_PROGRAM = "MODE_PROGRAM"
current_mode = MODE_ZIMBEL


button_clock = -1
zimbel_state = False
zimbel_button_light.value(zimbel_state)


zimbel_ready = False

BUTTON_HOLD_TIME = 1000 # 3000
BLINK_DURATION = 10000 # 30000 ?

DEBOUNCE_TIME = 250 # 50-250 ?
YIELD_TIME = 1 # 0-10?

midi_trigger_filename = 'midi_trigger.txt'
midi_trigger_bytes = []

stops_on = False

# Setup
# If the file already exists, save the contents to the trigger variables
if midi_trigger_filename in uos.listdir():
    with open(midi_trigger_filename, 'rb') as file:
        midi_trigger_bytes = list(file.read())
        print('Loaded midi trigger')
        print(midi_trigger_bytes)


def zimbel_on():
    global zimbel_state
    if not zimbel_state:
        zimbel_state = True
        zimbel_button_light.value(zimbel_state)
        print('Zimbel on')
        zimbel_ready_off()


def zimbel_off():
    global zimbel_state
    if zimbel_state:
        zimbel_state = False
        zimbel_button_light.value(zimbel_state)
        print('Zimbel off')
        zimbel_ready_off()


def zimbel_ready_on():
    zimbel_off()
    global zimbel_ready
    zimbel_ready = True
    prepare_button_light.value(zimbel_ready)
    print('Zimbel ready on')


def zimbel_ready_off():
    global zimbel_ready
    zimbel_ready = False
    prepare_button_light.value(zimbel_ready)
    print('Zimbel ready off')


def change_mode(new_mode):
    global current_mode, midi_trigger_on_off
    if current_mode != new_mode:
        print('Mode changed to', new_mode)
        current_mode = new_mode
        if current_mode == MODE_PROGRAM:
            # Perform these actions when entering program mode
            zimbel_off()
            midi_trigger_on_off = []


async def blink():
    global current_mode

    start_time = utime.ticks_ms()

    # Loop until duration has been reached or the mode changes of program mode
    while utime.ticks_diff(utime.ticks_ms(), start_time) < BLINK_DURATION and current_mode == MODE_PROGRAM:
        zimbel_button_light.value(not zimbel_button_light.value())
        await uasyncio.sleep_ms(200)
    # End loop with led off
    zimbel_button_light.value(False)
    
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


# Program change helper
def is_program_change(message_bytes):
    # Check if the message has at least three bytes
    if len(message_bytes) < 3:
        return False
    
    # Extract status byte and check if it is a Program Change message
    status_byte = message_bytes[0]
    if (status_byte & 0xF0) == 0xC0:  # Check if the most significant nibble is 1100 (Program Change)
        return True
    
    return False


# Sysex helper
def is_sysex(message_bytes):
    # Check if the message has at least two bytes
    if len(message_bytes) < 2:
        return False
    
    # Extract status bytes and check if it is the start or end of SysEx
    start_byte = message_bytes[0]
    end_byte = message_bytes[-1]
    
    if start_byte == 0xF0 and end_byte == 0xF7:
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


async def all_stops_off(input_bytes):
    return all(byte == 0 for byte in input_bytes)


async def midi_loop():
    global current_mode, zimbel_ready, midi_trigger_bytes, midi_trigger_filename, stops_on

    while True:
        if midi_uart.any():
            midi_bytes = list(midi_uart.read())
            
            # Handle midi data differently based on current mode
            if current_mode == MODE_ZIMBEL:
                # Filter out Active Sensing byte
                if midi_bytes == [0xFE]:
                    continue
                print('Midi message:', midi_bytes)
                print('Stops on:', stops_on)
                
                # Handle midi messages while in zimbel mode
                # i.e. listen for midi trigger

                # if program change
                if is_program_change(midi_bytes):
                    if bytes_match_trigger(midi_bytes):
                        zimbel_on()
                    else:
                        zimbel_off() # TODO: test if this is needed

                # if sysex
                if is_sysex(midi_bytes): # testing RODGERS sysex only for now
                    if await all_stops_off(midi_bytes[7:-2]):
                        stops_on = False
                    else:
                        stops_on = True

                    if bytes_match_trigger(midi_bytes[7:-2]):
                        zimbel_on()
                    else:
                        zimbel_off() # TODO: test if this is needed

                # if zimbel ready and note on
                if zimbel_ready and stops_on and is_note_on(midi_bytes):
                    print('zimbel ready and note on')
                    zimbel_on()

            elif current_mode == MODE_PROGRAM:
                # Handle midi messages while in program mode
                # i.e. listen for midi and assign to trigger
                # Filter out Active Sensing byte
                if midi_bytes != [0xFE]:
                    
                    if is_program_change(midi_bytes):
                        midi_trigger_bytes = midi_bytes

                    print('Program mode only working with Rodgers SYSEX right now')

                    # save midi trigger
                    midi_trigger_bytes = midi_bytes[7:-2]

                    # write to file
                    with open(midi_trigger_filename, 'wb') as file:
                        file.write(bytes(midi_trigger_bytes))
                    
                    print('Saved midi trigger:', midi_trigger_bytes)
                    change_mode(MODE_ZIMBEL)
        
        # Yield control to event loop
        await uasyncio.sleep_ms(YIELD_TIME)


async def zimbel_button_loop():
    global zimbel_button_state, button_clock, zimbel_state, current_mode

    while True:
        if zimbel_button.value() == 0:  # Button is being pressed
            if not zimbel_button_state:
                #print('Button pressed')
                zimbel_button_state = True
                button_clock = utime.ticks_ms()
                
                # Toggle zimbel state
                zimbel_off() if zimbel_state else zimbel_on()
                
                # Debounce after press
                await uasyncio.sleep_ms(DEBOUNCE_TIME)
            
            # Check if the button has been held for x number of ms
            if utime.ticks_diff(utime.ticks_ms(), button_clock) >= BUTTON_HOLD_TIME:
                change_mode(MODE_PROGRAM)
                await blink()
            
        else:  # Button is not being pressed
            if zimbel_button_state:
                #print('Button released')
                zimbel_button_state = False
        
        # Yield control to event loop
        await uasyncio.sleep_ms(YIELD_TIME)


async def prepare_button_loop():
    global prepare_button_state, zimbel_ready

    while True:
        if prepare_button.value() == 0:  # Button is being pressed
            if not prepare_button_state:
                # print('READY pressed')
                prepare_button_state = True
                
                # Toggle zimbel ready state
                zimbel_ready_off() if zimbel_ready else zimbel_ready_on()

                # Debounce after press
                await uasyncio.sleep_ms(DEBOUNCE_TIME)
            
        else:  # Button is not being pressed
            if prepare_button_state:
                # print('READY released')
                prepare_button_state = False
        
        # Yield control to event loop
        await uasyncio.sleep_ms(YIELD_TIME)


async def main():
    midi_loop_task = uasyncio.create_task(midi_loop())
    zimbel_button_loop_task = uasyncio.create_task(zimbel_button_loop())
    prepare_button_loop_task = uasyncio.create_task(prepare_button_loop())

    await uasyncio.gather(midi_loop_task, zimbel_button_loop_task, prepare_button_loop_task)


uasyncio.run(main())
