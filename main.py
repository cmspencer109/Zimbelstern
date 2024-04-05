import uasyncio
import uos
import utime
import random
from machine import Pin, UART, ADC


ZIMBEL_MELODY = 'cdfgacgdcafgcadf'

# Setting this to True will override the melody with an infinite, random, non-repeating sequence of notes
RANDOM_MELODY = True


# FOR DEBUGGING ONLY
# Set to False if needed for disabling certain features
# Set to True in production
BELLS_ENABLED = True
STAR_ENABLED = True


# Define board connections

pico_led = Pin(25, Pin.OUT)

bell_d = Pin(11, Pin.OUT)
bell_f = Pin(10, Pin.OUT)
bell_g = Pin(9, Pin.OUT)
bell_a = Pin(8, Pin.OUT)
bell_c = Pin(7, Pin.OUT)

bells = {
    'd': bell_d,
    'f': bell_f,
    'g': bell_g,
    'a': bell_a,
    'c': bell_c
}

midi_uart = UART(0, baudrate=31250, tx=Pin(0), rx=Pin(1))
star_uart = UART(1, baudrate=9600, tx=Pin(4))

prepare_button = Pin(13, Pin.IN, Pin.PULL_UP)
prepare_button_lamp = Pin(14, Pin.OUT)
prepare_button_state = False

zimbel_button = Pin(12, Pin.IN, Pin.PULL_UP)
zimbel_button_lamp = Pin(15, Pin.OUT)
zimbel_button_state = False

control_knob = ADC(26)
volume = 0 # Default value
tempo = 300 # Default value (bpm)


# Modes

ZIMBEL_MODE = 'ZIMBEL_MODE'
PROGRAM_MODE = 'PROGRAM_MODE'
current_mode = ZIMBEL_MODE


# Define and assign initial states

zimbel_button_clock = -1
prepare_button_clock = -1
zimbel_state = False
zimbel_button_lamp.value(zimbel_state)
zimbel_is_prepared = False
stops_on = False
zimbel_button_blinking = False
last_note_played = None

# Midi trigger variables

midi_trigger_filename = 'midi_trigger.txt'
midi_trigger_bytes = []


# Define constants

# Used to determine how long the button needs to be held to change to program mode (seconds)
# Suggested range: 2-5
BUTTON_HOLD_TIME = 1.5

# Used to set how long the button should blink while in program mode (seconds)
# Suggested range: 5-15
BLINK_DURATION = 10

# Used to debounce button presses (ms)
# Suggested range: 50-200
DEBOUNCE_TIME = 100

# Used to yield control to the event loop (ms)
YIELD_TIME = 1


def zimbel_on():
    global zimbel_state, current_mode
    if not zimbel_state and current_mode == 'ZIMBEL_MODE':
        zimbel_state = True
        zimbel_button_lamp.value(True)
        print('Zimbel on')
        prepare_zimbel_off()


def zimbel_off():
    global zimbel_state
    if zimbel_state:
        zimbel_state = False
        zimbel_button_lamp.value(False)
        print('Zimbel off')
        prepare_zimbel_off()


def prepare_zimbel_on():
    global zimbel_is_prepared, current_mode
    if not zimbel_is_prepared and current_mode == 'ZIMBEL_MODE':
        zimbel_off()
        zimbel_is_prepared = True
        prepare_button_lamp.value(True)
        print('Prepare on')


def prepare_zimbel_off():
    global zimbel_is_prepared
    zimbel_is_prepared = False
    prepare_button_lamp.value(False)
    print('Prepare off')


def change_mode(new_mode):
    global current_mode, zimbel_button_state, prepare_button_state

    zimbel_button_state = False
    prepare_button_state = False

    if current_mode != new_mode:
        print('Mode changed to', new_mode)
        if new_mode == PROGRAM_MODE:
            # Actions to perform when entering program mode:
            zimbel_off()
        current_mode = new_mode


def save_midi_trigger(midi_bytes):
    global midi_trigger_bytes, midi_trigger_filename
    midi_trigger_bytes = midi_bytes

    print(midi_bytes)

    with open(midi_trigger_filename, 'wb') as file:
        file.write(bytes(midi_trigger_bytes))
    
    if midi_bytes:
        print(f'Saved midi trigger: {midi_trigger_bytes}')
    else:
        print(f'Cleared midi trigger')


def load_midi_trigger_from_file():
    global midi_trigger_bytes, midi_trigger_filename
    
    if midi_trigger_filename in uos.listdir():
        with open(midi_trigger_filename, 'rb') as file:
            midi_trigger_bytes = list(file.read())

            if midi_trigger_bytes:
                print(f'Loaded midi trigger: {midi_trigger_bytes}')
            else:
                print(f'No midi trigger loaded')


async def blink():
    global current_mode, zimbel_button_blinking
    if not zimbel_button_blinking:
        zimbel_button_blinking = True
        print('blink called')

        start_time = utime.ticks_ms()

        # Loop until duration has been reached or the mode changes of program mode
        while utime.ticks_diff(utime.ticks_ms(), start_time) < BLINK_DURATION*1000 and current_mode == PROGRAM_MODE:
            zimbel_button_lamp.value(not zimbel_button_lamp.value())
            await uasyncio.sleep_ms(200)
        # End loop with led off
        zimbel_button_lamp.value(False)
        
        # If we reach this point and we are still in program mode, clear the trigger 
        if current_mode == PROGRAM_MODE:
            save_midi_trigger([])

        # Reset mode after completing loop
        change_mode(ZIMBEL_MODE)
        zimbel_button_blinking = False


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


def is_control_change(message_bytes):
    # Check if the message has at least two bytes
    if len(message_bytes) < 2:
        return False
    
    # Extract status byte and check if it is a Control Change message
    status_byte = message_bytes[0]
    if (status_byte & 0xF0) == 0xB0:  # Check if the most significant nibble is 1011 (Control Change)
        return True
    
    return False


def is_program_change(message_bytes):
    # Check if the message has at least two bytes
    if len(message_bytes) < 2:
        return False
    
    # Extract status byte and check if it is a Program Change message
    status_byte = message_bytes[0]
    if (status_byte & 0xF0) == 0xC0:  # Check if the most significant nibble is 1100 (Program Change)
        return True
    
    return False


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


def hex_to_bits(hex_number, total_width=8):
    binary_representation = bin(hex_number)[2:]
    return '0' * (total_width - len(binary_representation)) + binary_representation


def is_sublist(inner_list, outer_list):
    for i in range(len(outer_list) - len(inner_list) + 1):
        if outer_list[i:i+len(inner_list)] == inner_list:
            return True
    return False


def bytes_match_trigger(input_bytes):
    global midi_trigger_bytes

    print(f'Checking if input bytes match trigger')
    print(f'Input: {input_bytes}\nTrigger: {midi_trigger_bytes}')

    if is_sublist(midi_trigger_bytes, input_bytes) and midi_trigger_bytes != []:
        print(f'Match found')
        return True
    else:
        print(f'Not a match')
        return False


def all_stops_off_rodgers(input_bytes):
    rodgers_stops_bytes = input_bytes[7:-2]
    return all(byte == 0 for byte in rodgers_stops_bytes)


async def midi_loop():
    global current_mode, zimbel_is_prepared, midi_trigger_bytes, midi_trigger_filename, stops_on

    while True:
        if midi_uart.any():
            midi_bytes = list(midi_uart.read())
            
            # Filter out Active Sensing messages
            if midi_bytes == [0xFE]: continue
            # Strip out Active Sensing byte if it gets caught in another message
            if midi_bytes[0] == 0xFE: midi_bytes = midi_bytes[1:]

            # Handle midi messages differently based on current mode
            if current_mode == ZIMBEL_MODE:
                # print(f'Midi message: {midi_bytes}') # for testing
                # print('Stops on:', stops_on) # for testing

                # if program change (Used by numbered thumb and toe pistons on the organ)
                # One press to turn on, another press does nothing, 
                # but a different program change message will turn it off
                if is_program_change(midi_bytes):
                    print(f'Program Change: {midi_bytes}')
                    if bytes_match_trigger(midi_bytes):
                        zimbel_on()
                    else:
                        zimbel_off()

                # if control change (Used by midi coupler thumb pistons on the organ)
                # One press to turn on, another press to turn off (behaves like a toggle)
                if is_control_change(midi_bytes):
                    print(f'Control Change: {midi_bytes}')
                    if bytes_match_trigger(midi_bytes):
                        # Toggle zimbel on or off
                        if zimbel_state:
                            zimbel_off()
                        else:
                            zimbel_on()

                # if sysex (Used by Rodgers organs to send stop state messages)
                # Used to read the state of the stops to see if stops are on or off
                if is_sysex(midi_bytes):
                    # Only able to read Rodgers sysex messages
                    print(f'SysEx: {midi_bytes}')
                    if all_stops_off_rodgers(midi_bytes):
                        stops_on = False
                    else:
                        stops_on = True

                # if zimbel is prepared, stops are on, and a key is pressed
                if zimbel_is_prepared and stops_on and is_note_on(midi_bytes):
                    print('Zimbel is prepared and note on')
                    zimbel_on()

                # if general cancel
                if midi_bytes == [203, 19]:
                    print('General Cancel')
                    zimbel_off()
                    stops_on = False
                    continue

            elif current_mode == PROGRAM_MODE:
                if is_program_change(midi_bytes):
                    save_midi_trigger(midi_bytes)
                elif is_control_change(midi_bytes):
                    save_midi_trigger(midi_bytes)

                change_mode(ZIMBEL_MODE)
        
        # Yield control to event loop
        await uasyncio.sleep_ms(YIELD_TIME)


async def zimbel_button_loop():
    global zimbel_button_state, zimbel_button_clock, zimbel_state, current_mode

    while True:
        if zimbel_button.value() == 0:  # Button is being pressed
            if not zimbel_button_state:
                #print('Button pressed')
                zimbel_button_state = True
                zimbel_button_clock = utime.ticks_ms()
                
                # Toggle button lamp on button press
                if zimbel_state:
                    zimbel_button_lamp.value(False)
                else:
                    zimbel_button_lamp.value(True)
                
                # Debounce after press
                await uasyncio.sleep_ms(DEBOUNCE_TIME)
            
            # Check if the button has been held long enough to enter program mode
            if utime.ticks_diff(utime.ticks_ms(), zimbel_button_clock) >= BUTTON_HOLD_TIME*1000:
                change_mode(PROGRAM_MODE)
                await blink()
            
        else:  # Button is not being pressed
            if zimbel_button_state:
                #print('Button released')
                zimbel_button_state = False
                
                # Toggle zimbel state after button release
                if zimbel_state:
                    zimbel_off()
                else:
                    zimbel_on()
        
        # Yield control to event loop
        await uasyncio.sleep_ms(YIELD_TIME)


async def prepare_button_loop():
    global prepare_button_state, prepare_button_clock, zimbel_is_prepared

    while True:
        if prepare_button.value() == 0:  # Button is being pressed
            if not prepare_button_state:
                # print('Prepare button pressed')
                prepare_button_state = True
                prepare_button_clock = utime.ticks_ms()
                
                # Toggle zimbel prepared state
                if zimbel_is_prepared:
                    prepare_zimbel_off()
                else:
                    prepare_zimbel_on()

                # Debounce after press
                await uasyncio.sleep_ms(DEBOUNCE_TIME)

            # Do something special if the prepare button is held for 10 seconds...
            if utime.ticks_diff(utime.ticks_ms(), prepare_button_clock) >= 10000:
                await _()
            
        else:  # Button is not being pressed
            if prepare_button_state:
                # print('Prepare button released')
                prepare_button_state = False
        
        # Yield control to event loop
        await uasyncio.sleep_ms(YIELD_TIME)


async def control_knob_loop():
    global control_knob, volume, tempo

    while True:
        new_volume = get_volume()
        if new_volume != volume:
            volume = new_volume
            print(f'Volume: {volume}')

        # Yield control to event loop
        await uasyncio.sleep_ms(YIELD_TIME)


def get_volume():
    global control_knob

    min_value = 15
    max_value = 50

    pot_value = control_knob.read_u16()
    scaled_value = int(min_value + (pot_value / 65535) * (max_value - min_value))

    return scaled_value


def get_tempo():
    global tempo
    return tempo


async def bell_loop():
    global zimbel_state

    while True:
        if zimbel_state:
            if ZIMBEL_MELODY and not RANDOM_MELODY:
                await play_melody()
            else:
                await play_random_melody()
        
        # Yield control to event loop
        await uasyncio.sleep_ms(YIELD_TIME)


async def play_melody():
    global zimbel_state

    for note in ZIMBEL_MELODY:
        if zimbel_state:
            await play_note(note)


async def play_random_melody():
    global zimbel_state, bells, last_note_played

    random_note = random.choice(list(bells.keys()))

    # Prevent the same note from being played twice in a row
    while random_note == last_note_played:
        random_note = random.choice(list(bells.keys()))

    if zimbel_state:
        await play_note(random_note)


async def _():
    global zimbel_button_state, prepare_button_state

    zimbel_off()
    prepare_zimbel_off()

    print('''
    For all the saints who from their labors rest,
    All who their faith before the world confessed,
    Your name, O Jesus, be forever blest.
    Alleluia! Alleluia!
    ''')

    hymn = [
        ('c', 1), ('a', 1), ('g', 1), ('f', 3), ('c', 1), ('d', 1), ('f', 1), ('g', 1), ('c', 1), ('a', 2),
        ('g', 1), ('f', 1), ('g', 2), ('g', 2), ('f', 1), ('g', 1), ('f', 1), ('d', 1), ('c', 4), ('f', 2),
        ('f', 1), ('f', 1), ('c', 3), ('c', 1), ('g', 1), ('c', 1), ('g', 0.5), ('a', 0.5), ('g', 0.5), ('f', 0.5),
        ('g', 2), ('c', 2), ('d', 1), ('c', 0.5), ('a', 0.5), ('c', 2), ('a', 3), ('g', 0.5), ('a', 0.5),
        ('g', 1), ('a', 1), ('g', 2), ('f', 4),
    ]

    for note in hymn:
        await play_note(note=note[0], num_beats=note[1], tempo=120)


async def play_note(note, num_beats=1, tempo=tempo):
    global BELLS_ENABLED, volume, last_note_played

    beat_duration_in_seconds = (60 / tempo) * num_beats
    strike_duration_in_seconds = volume * 0.001
    sleep_duration_in_seconds = beat_duration_in_seconds - strike_duration_in_seconds

    # print(f'Playing {note.upper()} for {strike_duration_in_seconds} seconds')
    if BELLS_ENABLED:
        await strike_bell(bells[note], volume)
    
    # print(f'Sleeping for {sleep_duration_in_seconds} seconds')
    await uasyncio.sleep(sleep_duration_in_seconds)

    last_note_played = note


async def strike_bell(bell, strike_duration_in_ms):
    global pico_led
    
    bell.on()
    pico_led.on()

    # print(f'Striking bell for {strike_duration_in_ms} ms')
    await uasyncio.sleep_ms(strike_duration_in_ms)
    
    bell.off()
    pico_led.off()


async def star_loop():
    global zimbel_state, star_uart, STAR_ENABLED
    
    while True:
        if zimbel_state and STAR_ENABLED:
            # upper nibble determines on (F) or off (0)
            # lower nibble determines speed (0-F)
            star_byte = b'\xFF'
            star_uart.write(star_byte)
            # print(f'Sent {star_byte} to star uart')
            await uasyncio.sleep_ms(100)
        
        # Yield control to event loop
        await uasyncio.sleep_ms(YIELD_TIME)


def setup():
    global midi_trigger_filename, midi_trigger_bytes, volume, tempo

    volume = get_volume()
    tempo = get_tempo()

    print(f'Volume: {volume}')
    print(f'Tempo: {tempo}')

    load_midi_trigger_from_file()
    
    print('Zimbelstern ready')


async def main():
    setup()
    
    midi_loop_task = uasyncio.create_task(midi_loop())
    zimbel_button_loop_task = uasyncio.create_task(zimbel_button_loop())
    prepare_button_loop_task = uasyncio.create_task(prepare_button_loop())
    control_knob_loop_task = uasyncio.create_task(control_knob_loop())
    star_loop_task = uasyncio.create_task(star_loop())
    bell_loop_task = uasyncio.create_task(bell_loop())

    await uasyncio.gather(midi_loop_task, zimbel_button_loop_task, prepare_button_loop_task, 
                          control_knob_loop_task, star_loop_task, bell_loop_task)


uasyncio.run(main())
