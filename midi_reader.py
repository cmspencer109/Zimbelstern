import machine
import time

# Set up UART
uart = machine.UART(0, baudrate=31250, tx=0, rx=1)

while True:
    # Read data from UART
    if uart.any():
        midi_bytes = list(uart.read())
        
        # Filter out Active Sensing byte
        if midi_bytes == [0xFE]:
            continue

        print(midi_bytes)
    
    # Add a delay to avoid high CPU usage
    time.sleep_ms(10)