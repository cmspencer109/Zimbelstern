import machine
import utime

sensor_temp = machine.ADC(4)
conversion_factor = 3.3 / (65535)

while True:
    reading = sensor_temp.read_u16() * conversion_factor
    temperature = round(27 - (reading - 0.706)/0.001721,2)
    print("Temperature: ", temperature)
    utime.sleep(0.1)

