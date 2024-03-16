import machine
import uasyncio
import uos
import utime
from machine import Pin, UART, ADC
from ucollections import namedtuple

# TODO: Test Prepare button BEFORE stops engaged

# TODO: add support for general cancel

# TODO: handle ID when organ turns on ?
# organ id might reset every time its turned off/on
# maybe use whatever midi messages the organ sends when it turns on to reset the binding?

# DEBUGGING = True


BELLS_ENABLED = True

pico_led = Pin(25, Pin.OUT)

bell_d7 = Pin(11, Pin.OUT)
bell_f7 = Pin(10, Pin.OUT)
bell_g7 = Pin(9, Pin.OUT)
bell_a7 = Pin(8, Pin.OUT)
bell_c8 = Pin(7, Pin.OUT)

BellNote = namedtuple('BellNote', ['bell', 'volume'])

# BELL_SEQUENCE = [
#     [BellNote(bell=bell_d7, volume=1)],
#     [BellNote(bell=bell_f7, volume=1)],
#     [BellNote(bell=bell_g7, volume=1)],
#     [BellNote(bell=bell_a7, volume=1)],
#     [BellNote(bell=bell_c8, volume=1)]
# ]

# BELL_SEQUENCE = [
#     [BellNote(bell=bell_d7, volume=1), BellNote(bell=bell_f7, volume=0.5)],
#     [BellNote(bell=bell_a7, volume=1), BellNote(bell=bell_c8, volume=0.5)]
# ]

BELL_SEQUENCE = [
    [BellNote(bell=bell_d7, volume=1), BellNote(bell=bell_f7, volume=1)]
]

BUTTON_HOLD_TIME = 3000
BLINK_DURATION = 10000

DEBOUNCE_TIME = 100 # 50-250 ?
YIELD_TIME = 1 # 0-10?

midi_uart = UART(0, baudrate=31250, tx=Pin(0), rx=Pin(1))
star_uart = UART(1, baudrate=9600, tx=Pin(4))

prepare_button = Pin(13, Pin.IN, Pin.PULL_UP)
prepare_button_lamp = Pin(14, Pin.OUT)
prepare_button_state = False

zimbel_button = Pin(12, Pin.IN, Pin.PULL_UP)
zimbel_button_lamp = Pin(15, Pin.OUT)
zimbel_button_state = False

volume_pot = ADC(26)
volume = 0

# Modes
ZIMBEL_MODE = "ZIMBEL_MODE"
PROGRAM_MODE = "PROGRAM_MODE"
current_mode = ZIMBEL_MODE


button_clock = -1
zimbel_state = False
zimbel_button_lamp.value(zimbel_state)


zimbel_ready = False



midi_trigger_filename = 'midi_trigger.txt'
midi_trigger_bytes = []

stops_on = False

zimbel_button_blinking = False

# Setup
# If the file already exists, save the contents to the trigger variables
if midi_trigger_filename in uos.listdir():
    with open(midi_trigger_filename, 'rb') as file:
        midi_trigger_bytes = list(file.read())
        print('Loaded midi trigger')
        print(midi_trigger_bytes)


def zimbel_on():
    global zimbel_state, current_mode
    if not zimbel_state and current_mode == 'ZIMBEL_MODE':
        zimbel_state = True
        zimbel_button_lamp.value(zimbel_state)
        print('Zimbel on')
        zimbel_ready_off()
        # await bell_loop() # TODO move to top level task


def zimbel_off():
    global zimbel_state
    if zimbel_state:
        zimbel_state = False
        zimbel_button_lamp.value(zimbel_state)
        print('Zimbel off')
        zimbel_ready_off()


def zimbel_ready_on():
    zimbel_off()
    global zimbel_ready
    zimbel_ready = True
    prepare_button_lamp.value(zimbel_ready)
    print('Zimbel ready on')


def zimbel_ready_off():
    global zimbel_ready
    zimbel_ready = False
    prepare_button_lamp.value(zimbel_ready)
    print('Zimbel ready off')


def change_mode(new_mode):
    global current_mode
    if current_mode != new_mode:
        print('Mode changed to', new_mode)
        current_mode = new_mode
        if current_mode == PROGRAM_MODE:
            # Actions to perform when entering program mode:
            zimbel_off()


async def blink():
    global current_mode, zimbel_button_blinking
    if not zimbel_button_blinking:
        zimbel_button_blinking = True
        print('blink called')

        start_time = utime.ticks_ms()

        # Loop until duration has been reached or the mode changes of program mode
        while utime.ticks_diff(utime.ticks_ms(), start_time) < BLINK_DURATION and current_mode == PROGRAM_MODE:
            zimbel_button_lamp.value(not zimbel_button_lamp.value())
            await uasyncio.sleep_ms(200)
        # End loop with led off
        zimbel_button_lamp.value(False)
        
        # Reset mode after completing loop
        change_mode(ZIMBEL_MODE)
        zimbel_button_blinking = False


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
            if current_mode == ZIMBEL_MODE:
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

            elif current_mode == PROGRAM_MODE:
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
                    change_mode(ZIMBEL_MODE)
        
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
                if zimbel_state:
                    zimbel_off()
                else:
                    zimbel_on()
                
                # Debounce after press
                await uasyncio.sleep_ms(DEBOUNCE_TIME)
            
            # Check if the button has been held for x number of ms
            if utime.ticks_diff(utime.ticks_ms(), button_clock) >= BUTTON_HOLD_TIME:
                change_mode(PROGRAM_MODE)
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
                if zimbel_ready:
                    zimbel_ready_off()
                else:
                    zimbel_ready_on()

                # Debounce after press
                await uasyncio.sleep_ms(DEBOUNCE_TIME)
            
        else:  # Button is not being pressed
            if prepare_button_state:
                # print('READY released')
                prepare_button_state = False
        
        # Yield control to event loop
        await uasyncio.sleep_ms(YIELD_TIME)


async def volume_pot_loop():
    global volume, volume_pot

    while True:
        volume_pot_value = volume_pot.read_u16()
        
        # Reverse the mapping for pulse duration (e.g., 100 to 10 ms)
        volume = int(((65535 - volume_pot_value) / 65535) * 90) + 10
        # print(f'Volume {volume_pot_value}')

        # Yield control to event loop
        await uasyncio.sleep_ms(YIELD_TIME)


async def bell_loop():
    global zimbel_state, BELLS_ENABLED, BELL_SEQUENCE

    while True:
        if zimbel_state and BELLS_ENABLED:
            for chord in BELL_SEQUENCE:
                for note in chord:
                    print(f'Playing {note}')
                    await play_bell_note(*note)
                print('Sleeping for 1s')
                await uasyncio.sleep_ms(1500)
        
        # Yield control to event loop
        await uasyncio.sleep_ms(YIELD_TIME)


async def play_bell_note(bell, volume_factor):
    global pico_led, volume

    bell.on()
    pico_led.on()

    print(f'Pulsing for {volume*volume_factor}ms')
    await uasyncio.sleep_ms(volume*volume_factor)
    
    bell.off()
    pico_led.off()


async def star_loop():
    global zimbel_state, star_uart
    
    while True:
        if zimbel_state:
            star_byte = b'\xFF'
            star_uart.write(star_byte)
            # print(f'Sent {star_byte} to star uart')
            await uasyncio.sleep_ms(100)
        
        # Yield control to event loop
        await uasyncio.sleep_ms(YIELD_TIME)


async def main():
    midi_loop_task = uasyncio.create_task(midi_loop())
    zimbel_button_loop_task = uasyncio.create_task(zimbel_button_loop())
    prepare_button_loop_task = uasyncio.create_task(prepare_button_loop())
    volume_pot_loop_task = uasyncio.create_task(volume_pot_loop())
    star_loop_task = uasyncio.create_task(star_loop())
    bell_loop_task = uasyncio.create_task(bell_loop())

    await uasyncio.gather(midi_loop_task, zimbel_button_loop_task, prepare_button_loop_task, 
                          volume_pot_loop_task, star_loop_task, bell_loop_task)


uasyncio.run(main())
