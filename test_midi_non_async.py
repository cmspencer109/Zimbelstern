import time


midi_uart = machine.UART(0, baudrate=31250, tx=0, rx=1)

def read_midi():
    if midi_uart.any():
        data = midi_uart.read()
        
        # Check if the received byte is not an Active Sensing message (0xFE)
        if data != b'\xfe':
            #print("MIDI message: {}".format(data.hex()))
            print("MIDI message: {}".format(data))

while True:
    read_midi()
    print('going to sleep for 5 seconds')
    time.sleep(5)


