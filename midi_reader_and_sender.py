import uasyncio as asyncio
import utime as time
import machine
from machine import Pin 


# Set up UART
uart = machine.UART(0, baudrate=31250, tx=0, rx=1)
button = Pin(15, Pin.IN, Pin.PULL_UP)
button_state = False


async def str_to_byte_list(s):
    return [int(h, 16) for h in s.split()]


async def send_sysex():
    global uart
    
    sysex_msg = await str_to_byte_list("F0 41 10 30 12 01 00 08 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 77 F7")
    # sysex_off = await str_to_byte_list("F0 41 10 30 12 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 7F F7")

    uart.write(bytearray(sysex_msg))
    print('Sent\t', sysex_msg)

    # print('Sleep 1 second')
    # await asyncio.sleep(1)

    # print(f'Sending:  {sysex_off}')
    # uart.write(bytearray(sysex_off))


async def read_midi():
    while True:
        # Read data from UART
        if uart.any():
            midi_bytes = list(uart.read())
            
            # Filter out Active Sensing byte
            if midi_bytes == [0xFE]:
                continue

            print('Received\t', midi_bytes)
        
        # Yield control to event loop
        await asyncio.sleep_ms(1)


async def read_button():
    global button, button_state
    
    while True:
        if button.value() == 0:  # Button is being pressed
            if not button_state:
                # print('READY pressed')
                button_state = True
                
                await send_sysex()

                # Debounce after press
                await asyncio.sleep_ms(50)
            
        else:  # Button is not being pressed
            if button_state:
                # print('READY released')
                button_state = False
        
        # Yield control to event loop
        await asyncio.sleep_ms(1)


async def main():
    # Create task handlers
    read_midi_handler = asyncio.create_task(read_midi())
    read_button_handler = asyncio.create_task(read_button())

    # Run the event loop
    await asyncio.gather(read_midi_handler, read_button_handler)

# Run the main function to start the event loop
asyncio.run(main())
