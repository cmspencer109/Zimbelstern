import uasyncio
import time
import random
from machine import Pin, UART, ADC


# If a melody is not specified, a random melody will be played
DELAY_BETWEEN_MELODY_REPEAT = False
ZIMBEL_MELODY = ''
# ZIMBEL_MELODY = 'cdfgacgdcafgcadf' # 16 note pattern
# ZIMBEL_MELODY = 'dfgac' # ascending
# ZIMBEL_MELODY = 'cagfd' # descending 
# ZIMBEL_MELODY = 'dfgacagf' # ascending and descending

FADE_VOLUME_START = True
FADE_TEMPO_START = True
FADE_IN_DURATION = 3 # seconds
tempo = 300 # bpm
STARTING_TEMPO = tempo-60 # bpm
PLAY_SECOND_NOTE = False
SECOND_NOTE_DELAY = 0 # ms

# FOR DEBUGGING ONLY
# Set to False if needed for disabling certain features
# Set to True in production
BELLS_ENABLED = True
STAR_ENABLED = True


# Define board connections

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

note_weights = {key: 1 for key in bells.keys()}

midi_uart = UART(0, baudrate=31250, tx=Pin(0), rx=Pin(1))
star_uart = UART(1, baudrate=9600, tx=Pin(4))

prepare_button = Pin(13, Pin.IN, Pin.PULL_UP)
prepare_button_lamp = Pin(14, Pin.OUT)
prepare_button_state = False

zimbel_button = Pin(12, Pin.IN, Pin.PULL_UP)
zimbel_button_lamp = Pin(15, Pin.OUT)
zimbel_button_state = False

volume_knob = ADC(26)
volume = 0

beats_per_second = tempo // 60
num_beats_to_fade = int(beats_per_second * FADE_IN_DURATION)
faded_volumes = []
faded_tempos = []


# Define and assign initial states

prepare_button_clock = -1
zimbel_state = False
zimbel_playing = False
zimbel_button_lamp.value(False)
zimbel_is_prepared = False
stops_on = False


# Define constants

# Used to debounce button presses (ms)
# Suggested range: 50-200
DEBOUNCE_TIME = 100

# Used to yield control to the event loop (ms)
YIELD_TIME = 1

# Set volume range of potentiometer
# Value is the amount of time each electromagnet is powered on for (ms)
ABSOLUTE_MIN_VOLUME = 12
MIN_VOLUME = 15
MAX_VOLUME = 40


def get_spread(min_value, max_value, num_steps):
    step = (max_value - min_value) / (num_steps - 1)
    return [min_value + step * i for i in range(num_steps)]


def zimbel_on():
    global zimbel_state, zimbel_button_lamp, faded_volumes, faded_tempos
    
    if not zimbel_state:
        faded_volumes = get_spread(ABSOLUTE_MIN_VOLUME, volume, num_beats_to_fade)
        faded_tempos = get_spread(STARTING_TEMPO, tempo, num_beats_to_fade)

        zimbel_state = True
        zimbel_button_lamp.value(True)
        print('Zimbel on')
        prepare_zimbel_off()


def zimbel_off():
    global zimbel_state, zimbel_playing, zimbel_button_lamp

    if zimbel_state:
        zimbel_state = False
        zimbel_playing = False
        zimbel_button_lamp.value(False)
        print('Zimbel off')
        prepare_zimbel_off()


def prepare_zimbel_on():
    global zimbel_is_prepared

    if not zimbel_is_prepared:
        zimbel_off()
        zimbel_is_prepared = True
        prepare_button_lamp.value(True)
        print('Prepare on')


def prepare_zimbel_off():
    global zimbel_is_prepared

    zimbel_is_prepared = False
    prepare_button_lamp.value(False)
    print('Prepare off')


def is_note_on(midi_bytes):
    if len(midi_bytes) < 3:
        return False

    # Check if the status byte indicates a Note On message
    if (midi_bytes[0] & 0xF0) == 0x90:
        # Check if the velocity is greater than 0
        if midi_bytes[2] > 0:
            return True

    return False


def is_sysex(message_bytes):
    if len(message_bytes) < 2:
        return False
    
    # Extract status bytes and check if it is the start or end of SysEx
    start_byte = message_bytes[0]
    end_byte = message_bytes[-1]
    
    if start_byte == 0xF0 and end_byte == 0xF7:
        return True
    
    return False


def all_stops_off_rodgers(input_bytes):
    rodgers_stops_bytes = input_bytes[7:-2]
    return all(byte == 0 for byte in rodgers_stops_bytes)


async def midi_loop():
    global zimbel_is_prepared, stops_on

    while True:
        if midi_uart.any():
            midi_bytes = list(midi_uart.read())
            
            # Filter out Active Sensing messages
            if midi_bytes == [0xFE]: continue
            # Strip out Active Sensing byte if it gets caught in another message
            if midi_bytes[0] == 0xFE: midi_bytes = midi_bytes[1:]

            # Process MIDI message:

            # If SysEx (Used by Rodgers organs to send stop state messages)
            # Used to read the state of the stops to see if stops are on or off
            if is_sysex(midi_bytes):
                # Only able to read Rodgers SysEx messages
                if all_stops_off_rodgers(midi_bytes):
                    stops_on = False
                else:
                    stops_on = True

            # If zimbel is prepared, stops are on, and a key is pressed
            if zimbel_is_prepared and stops_on and is_note_on(midi_bytes):
                print('Zimbel is prepared and note on')
                zimbel_on()

            # If general cancel
            if midi_bytes == [203, 19]:
                print('General Cancel')
                zimbel_off()
                stops_on = False
                continue

        # Yield control to event loop
        await uasyncio.sleep_ms(YIELD_TIME)


async def zimbel_button_loop():
    global zimbel_button_state, zimbel_state

    while True:
        if zimbel_button.value() == 0:  # Button is being pressed
            if not zimbel_button_state:
                #print('Button pressed')
                zimbel_button_state = True
                
                # Toggle zimbel state
                if zimbel_state:
                    zimbel_off()
                else:
                    zimbel_on()
                
                # Debounce after press
                await uasyncio.sleep_ms(DEBOUNCE_TIME)
            
        else:  # Button is not being pressed
            if zimbel_button_state:
                #print('Button released')
                zimbel_button_state = False
        
        # Yield control to event loop
        await uasyncio.sleep_ms(YIELD_TIME)


async def prepare_button_loop():
    global prepare_button_state, prepare_button_clock, zimbel_is_prepared

    while True:
        if prepare_button.value() == 0:  # Button is being pressed
            if not prepare_button_state:
                # print('Prepare button pressed')
                prepare_button_state = True
                prepare_button_clock = time.ticks_ms()
                
                # Toggle zimbel prepared state
                if zimbel_is_prepared:
                    prepare_zimbel_off()
                else:
                    prepare_zimbel_on()

                # Debounce after press
                await uasyncio.sleep_ms(DEBOUNCE_TIME)

            # Do something special if the prepare button is held for 5 seconds...
            if time.ticks_diff(time.ticks_ms(), prepare_button_clock) >= 5000:
                await _()
            
        else:  # Button is not being pressed
            if prepare_button_state:
                # print('Prepare button released')
                prepare_button_state = False
        
        # Yield control to event loop
        await uasyncio.sleep_ms(YIELD_TIME)


async def volume_knob_loop():
    global volume_knob, volume, tempo

    while True:
        pot_value = volume_knob.read_u16()
        new_volume = int(MIN_VOLUME + (pot_value / 65535) * (MAX_VOLUME - MIN_VOLUME))
        
        if new_volume != volume:
            volume = new_volume
            # print(f'Volume: {volume}')

        # Yield control to event loop
        await uasyncio.sleep_ms(YIELD_TIME)


async def bell_loop():
    global zimbel_state, zimbel_playing

    while True:
        if zimbel_state and not zimbel_playing:
            zimbel_playing = True

            if ZIMBEL_MELODY:
                await play_zimbel_melody(ZIMBEL_MELODY)
            else:
                await play_random_melody()
        
        # Yield control to event loop
        await uasyncio.sleep_ms(YIELD_TIME)


async def star_loop():
    global zimbel_state, star_uart
    
    while True:
        if zimbel_state and STAR_ENABLED:
            # upper nibble determines on (F) or off (0)
            # lower nibble determines speed (0-F)
            star_byte = b'\xFF'
            star_uart.write(star_byte)
            # print(f'Sent {star_byte} to star uart')
            await uasyncio.sleep_ms(10)
        
        # Yield control to event loop
        await uasyncio.sleep_ms(YIELD_TIME)


def get_beat_duration(current_beat):
    global tempo, num_beats_to_fade, faded_tempos

    if FADE_TEMPO_START and current_beat < num_beats_to_fade:
        working_tempo = int(faded_tempos[current_beat])
    else:
        working_tempo = tempo
    
    return 60 / working_tempo


def get_working_volume(current_beat):
    global volume, num_beats_to_fade, faded_volumes

    if FADE_VOLUME_START and current_beat < num_beats_to_fade:
        working_volume = int(faded_volumes[current_beat])
    else:
        working_volume = volume
    
    return working_volume


async def play_zimbel_melody(melody):
    global volume, tempo, zimbel_state

    while zimbel_state:
        for note in melody:
            beat_duration_in_ms = (60 / tempo)*1000
            sleep_duration_in_ms = beat_duration_in_ms-volume

            if zimbel_state:
                await strike_bell(note, volume)
                time.sleep_ms(int(sleep_duration_in_ms))


async def play_hymn_melody(melody, override_volume=None, override_tempo=None, repeat=False):
    global volume, tempo

    working_volume = override_volume if override_volume else volume
    working_tempo = override_tempo if override_tempo else tempo

    for note in melody:
        note_name = note[0]
        note_duration = note[1]
        beat_duration_in_ms = (60 / working_tempo)*note_duration*1000
        sleep_duration_in_ms = beat_duration_in_ms-working_volume

        await strike_bell(note_name, working_volume)
        time.sleep_ms(int(sleep_duration_in_ms))


async def play_random_melody():
    global zimbel_state
    
    beat_counter = 0
    start_time = time.ticks_ms()

    while zimbel_state:
        beat_duration = get_beat_duration(current_beat=beat_counter)
        working_volume = get_working_volume(current_beat=beat_counter)

        if time.ticks_diff(time.ticks_ms(), start_time) >= beat_duration*1000:
            start_time = time.ticks_ms()
            beat_counter += 1

            # Play a random note
            random_note = get_random_note_by_weight()
            await strike_bell(random_note, working_volume)

            if PLAY_SECOND_NOTE:
                # Play a second random note shortly after the first
                await uasyncio.sleep_ms(random.randint(0,SECOND_NOTE_DELAY))
                random_note = get_random_note_by_weight()
                await strike_bell(random_note, ABSOLUTE_MIN_VOLUME)
        
        await uasyncio.sleep_ms(YIELD_TIME)


def get_random_note():
    global note_weights

    # pick a random note whose weight is not 0 to avoid repeats
    available_notes = [note for note, weight in note_weights.items() if weight != 0]
    random_note = random.choice(available_notes)

    # assign the picked note weight to 0
    note_weights[random_note] = 0

    # reset the weight of all other notes to 1
    for note in note_weights:
        if note != random_note:
            note_weights[note] = 1

    return random_note


def get_random_note_by_weight():
    global note_weights

    # create a weighted list where each note appears as many times as its weight
    # exclude notes with a weight of 0 to avoid repeats
    weighted_list_of_notes = [note for note, weight in note_weights.items() for _ in range(weight) if weight > 0]

    # pick a random note from the weighted list
    random_note = random.choice(weighted_list_of_notes)

    # assign the picked note weight to 0 or less
    # assigning to 0 will allow all 4 bells to be picked from
    # assigning to -1 will allow the 3 oldest bells to be picked from
    # assigning to -2 will allow the 2 oldest bells to be picked from
    # assigning to -3 forces the oldest bell to be picked, inherently removing the randomness
    # -3 and lower should not be used
    note_weights[random_note] = -1

    # increase the weight of all other notes by 1
    for note in note_weights:
        if note != random_note:
            note_weights[note] += 1
    
    return random_note


async def strike_bell(note, strike_duration_in_ms):
    global bells

    if BELLS_ENABLED:
        print(f'Striking bell for {strike_duration_in_ms} ms')
        bells[note].on()
        await uasyncio.sleep_ms(strike_duration_in_ms)
        bells[note].off()


async def _():
    global zimbel_button_state, prepare_button_state, FADE_VOLUME_START

    zimbel_off()
    prepare_zimbel_off()
    old_fade_volume_start_state = FADE_VOLUME_START
    FADE_VOLUME_START = False

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

    await play_hymn_melody(hymn, override_tempo=120)
    
    FADE_VOLUME_START = old_fade_volume_start_state


async def main():
    tasks = [
        uasyncio.create_task(midi_loop()),
        uasyncio.create_task(zimbel_button_loop()),
        uasyncio.create_task(prepare_button_loop()),
        uasyncio.create_task(volume_knob_loop()),
        uasyncio.create_task(bell_loop()),
        uasyncio.create_task(star_loop())
    ]

    await uasyncio.gather(*tasks)


uasyncio.run(main())
