import machine
import uasyncio

star_uart = machine.UART(0, baudrate=9600, rx=1)

async def uart_listener():
    global star_uart

    while True:
        if star_uart.any(): # is this needed
            byte_received = star_uart.read(1)
            if byte_received == b'\xff':
                print("Received 0xff byte")
            elif byte_received == b'\x00':
                print("Received 0x00 byte")

async def motor():
    pass

async def main():
    uart_loop_task = uasyncio.create_task(uart_listener())
    motor_loop_task = uasyncio.create_task(motor())
    
    await uasyncio.gather(uart_loop_task, motor_loop_task)

uasyncio.run(main())
