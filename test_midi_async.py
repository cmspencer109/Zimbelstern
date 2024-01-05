import uasyncio as asyncio

midi_uart = machine.UART(0, baudrate=31250, tx=0, rx=1)

async def read_midi_task():
    while True:
        if midi_uart.any():
            data = midi_uart.read()
            
            # Check if the received byte is not an Active Sensing message (0xFE)
            if data != b'\xfe':
                print("MIDI message: {}".format(data))
        
        # Sleep for a short duration to avoid blocking the event loop
        await asyncio.sleep_ms(10)

async def print_message_task():
    while True:
        print("Printing a message every 5 seconds")
        await asyncio.sleep(5)

async def main():
    # Create and run both tasks concurrently
    midi_task_handler = asyncio.create_task(read_midi_task())
    print_task_handler = asyncio.create_task(print_message_task())
    
    # Run the event loop
    await asyncio.gather(midi_task_handler, print_task_handler)

# Run the main function to start the event loop
asyncio.run(main())
