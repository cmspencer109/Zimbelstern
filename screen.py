from machine import Pin, I2C
import ssd1306
import utime

# ssd1306 resources:
# https://github.com/stlehmann/micropython-ssd1306/blob/master/ssd1306.py
# https://docs.micropython.org/en/latest/esp8266/tutorial/ssd1306.html

# Define the I2C pins
i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=400000)

# Create an SSD1306 object
display_width = 128
display_height = 64
display = ssd1306.SSD1306_I2C(display_width, display_height, i2c)

# Clear the display
display.fill(0)
display.show()

display.fill(0)
display.fill_rect(0, 0, 32, 32, 1)
display.fill_rect(2, 2, 28, 28, 0)
display.vline(9, 8, 22, 1)
display.vline(16, 2, 22, 1)
display.vline(23, 8, 22, 1)
display.fill_rect(26, 24, 2, 4, 1)
display.text('MicroPython', 40, 0, 1)
display.text('SSD1306', 40, 12, 1)
display.text('OLED 128x64', 40, 24, 1)
display.show()

# Wait for a few seconds
#utime.sleep(5)

# Clear the display again
#oled.fill(0)
#oled.show()
