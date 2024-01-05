import machine
import time

# Set up UART
uart = machine.UART(0, baudrate=31250, tx=0, rx=1)

while True:
    # Read data from UART
    if uart.any():
        data = uart.read()
        
        # Check if the received byte is not an Active Sensing message (0xFE)
        if data != b'\xfe':
            print("Received data: {}".format(data.hex()))
    
    # Add a delay to avoid high CPU usage
    time.sleep_ms(10)