from machine import Pin,I2C
import rfd77402
from ssd1306 import SSD1306_I2C

i2c = I2C(sda=Pin("Y10"), scl=Pin("Y9"))
oled = SSD1306_I2C(128, 32, i2c, addr=0x3c)
tof = rfd77402.RFD77402(addr=0x4C,i2c=i2c)

pyb.delay(100)
tof.begin()

while True:
    tof.takeMeasurement()
    t = tof.getDistance()
    oled.fill(0)
    oled.text("Distance is:", 0, 0)
    oled.text(str(t) + " mm", 0, 20)
    oled.show()
    pyb.delay(100)

