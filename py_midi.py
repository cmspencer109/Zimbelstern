# MIDI commands
NOTE_ON = 0x90
NOTE_OFF = 0x80
CONTROL_CHANGE = 0xB0
PROGRAM_CHANGE = 0xC0
SYS_EX = 0xF0

# Rodgers SysEx Header
RODGERS_BEGIN_SYS_EX = 0xF0  # Begin System Exclusive 
RODGERS_SYS_EX_ID = 0x41     # Roland/Rodgers SysEx ID 
RODGERS_DEVICE_ID = 0x10     # Device ID
RODGERS_MODEL_ID = 0x30      # Model ID (30 = organ) 
RODGERS_DATA_SET = 0x12      # Data Set Command
RODGERS_SYS_EX_HEADER = [RODGERS_BEGIN_SYS_EX, RODGERS_SYS_EX_ID, RODGERS_DEVICE_ID, RODGERS_MODEL_ID, RODGERS_DATA_SET]
# Rodgers Subcommand bytes
RODGERS_STOP_CHANGE = 0x01
RODGERS_MEMORY_DUMP = 0x03

# Table may be incomplete
# Data from a Rodgers 702 manual
RODGERS_STOP_SYS_EX_CODE_ASSIGNMENTS = {
    'GREAT': {
        (0, 3): "8' Principal",
        (1, 0): "8' Nason Gedackt",
        (1, 2): "8' Flauto Dolce",
        (1, 3): "8' Flute Celeste II",
        (1, 5): "4' Octave",
        (1, 6): "4' Spitzflote",
        (2, 1): "2' Super Octave",
        (2, 3): "1 1/3' Quintflote",
        (2, 6): "IV Mixture",
        (3, 4): "8' Cromorne",
        (4, 1): "Chimes",
        (1, 2): "16' Bourdon",
    },
    'SWELL': {
        (8, 0): "8' Viola",
        (8, 1): "8' Viola Celeste II",
        (8, 4): "8' Bourdon",
        (9, 3): "4' Prestant",
        (9, 4): "4' Koppelflote",
        (9, 5): "2 2/3' Nazard",
        (10, 0): "2' Blockflote",
        (10, 4): "IV Plein Jeu",
        (10, 6): "16' Contre Basson",
        (11, 1): "8' Trompette",
        (11, 2): "8' Hautbois",
        (10, 1): "1 3/5' Tierce",
    },
    'PEDAL': {
        (21, 3): "16' Principal",
        (21, 4): "16' Subbass",
        (22, 2): "8' Octave",
        (22, 4): "8' Gedackt",
        (22, 6): "4' Choralbass",
        (24, 2): "16' Fagott",
        (24, 6): "4' Rohr Schalmei",
    },
    'COUPLERS_AND_OTHER_CONTROLS': {
        (25, 3): "Great to Pedal",
        (25, 5): "Swell to Pedal",
        (26, 6): "Swell to Great",
        (31, 3): "Swell Flute Tremulant Full",
        (4, 4): "Great Tremulant",
        (11, 6): "Swell Tremulant",
    }
}

# Example usage:
print(RODGERS_STOP_SYS_EX_CODE_ASSIGNMENTS['GREAT'][(0, 3)])  # Output: "8' Principal"
print(RODGERS_STOP_SYS_EX_CODE_ASSIGNMENTS['SWELL'][(8, 0)])  # Output: "8' Viola"

# filename = 'midi_trigger.txt'
# midi_trigger_byte_index = -1
# midi_trigger_bit_index = -1

# def store_trigger(bytes):
#     global midi_trigger_byte_index, midi_trigger_bit_index

#     byte_index, bit_index = identify_byte_and_bit_indexes(bytes)
    
#     with open(filename, 'w') as file:
#         file.write(f'{byte_index} {bit_index}')
#         midi_trigger_byte_index = byte_index
#         midi_trigger_bit_index = bit_index
#         print('Midi trigger saved')


def store_midi_trigger(data_bytes):
    # Get the first non-zero byte
    for byte_index, byte in enumerate(data_bytes):
        if byte != 0:
            # Get bits
            bits = format(byte, '08b')
            # Iterate from right to left to find index of first set bit
            for bit_index, bit in enumerate(bits[::-1]):
                if bit == '1':
                    set_bit_index = 7 - bit_index
                    print('Byte: {} Bit: {}'.format(byte_index, bit_index))
                    return byte_index, bit_index
            break
    else:
        print('No non-zero bytes were found')
        # return -1, -1


def rodgers_handle_stop_change(data_bytes):
    print(f'Stop change unhandled. Data bytes: {data_bytes}')


def handle_note_on(note, velocity):
    print(f'Note On - Note: {note}, Velocity: {velocity}')


def handle_note_off(note, velocity):
    print(f'Note Off - Note: {note}, Velocity: {velocity}')


def handle_control_change(control_number, value):
    print(f'Control Change - Control Number: {control_number}, Value: {value}')


def handle_program_change(program_number):
    print(f'Program Change - Program Number: {program_number}')


def handle_sysex(bytes):
    # System exclusive messages are manufacturer specific
    # Each manufacturer needs to be handled specifically based on their sysex implementation

    # Rodgers
    if len(bytes) >= 5 and bytes[:5] == RODGERS_SYS_EX_HEADER:
        print('Rodgers sysex')

        bytes = bytes[5:] # Trim header bytes

        subcommand_byte = bytes[0]
        offset_byte = bytes[1] # unused
        data_bytes = bytes[2:-2]
        end_sys_ex_byte = bytes[-1] # unused
        checksum_byte = bytes[-2] # unused

        if offset_byte != 0:
            print(f'Alert! Offset byte is {offset_byte}. Offset byte logic is unsupported')

        if subcommand_byte == RODGERS_STOP_CHANGE:
            print('Rodgers stop change')
            rodgers_handle_stop_change(data_bytes)
        elif subcommand_byte == RODGERS_MEMORY_DUMP:
            print('Memory dump is unsupported')
        else:
            print(f'Unsupported subcommand byte {subcommand_byte}')
        
    elif False:
        # Add support for another manufacturer here
        pass
    else:
        print(f'Unsupported sysex message {bytes}')


def handle_midi_message(bytes):
    if not bytes:
        print('Empty midi message, nothing to handle')
        return

    status_byte = bytes[0]
    command = status_byte & 0xF0 # Upper 4 bits describe the command (MSB is always 1)

    if command == NOTE_ON:
        handle_note_on(bytes[1], bytes[2])
    elif command == NOTE_OFF:
        handle_note_off(bytes[1], bytes[2])
    elif command == CONTROL_CHANGE:
        handle_control_change(bytes[1], bytes[2])
    elif command == PROGRAM_CHANGE:
        handle_program_change(bytes[1])
    elif command == SYS_EX:
        handle_sysex(bytes[1:])
    else:
        print(f'Unsupported midi message beginning with status byte {status_byte}')


# test:
# byte_string = b'\xf0A\x100\x12\x01\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00w\xf7'
# bytes = list(byte_string)
# handle_midi_message(bytes)

