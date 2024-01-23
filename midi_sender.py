import machine
import time

# Set up UART
uart = machine.UART(0, baudrate=31250, tx=0, rx=1)

# print('Testing middle C on the Great for 1 second')
# uart.write(bytearray([0x9B, 0x48, 0x40])))
# time.sleep(1)
# uart.write(bytearray([0x9B, 0x48, 0x00]))

def str_to_byte_list(s):
    return [int(h, 16) for h in s.split()]

sysex_msg = str_to_byte_list("F0 41 10 30 12 01 00 08 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 77 F7")
sysex_off = str_to_byte_list("F0 41 10 30 12 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 7F F7")

print(f'Sending:  {sysex_msg}')
uart.write(bytearray(sysex_msg))

print('Sleeping for 1 second')
time.sleep(1)

uart.write(bytearray(str_to_byte_list("F0 41 10 30 12 01 00 00 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 7E F7")))
time.sleep(1)

print(f'Sending:  {sysex_off}')
uart.write(bytearray(sysex_off))
