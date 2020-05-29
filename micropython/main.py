"""
Demo code for RFD77402 TOF sensor
Auther: Alex Chu
Website: www.smart-prototyping.com
Email: shop@smart-prototyping.com
TOF RFD77402 product link: https://www.smart-prototyping.com/Zio-TOF-Distance-Sensor-RFD77402.html
Display product link: https://www.smart-prototyping.com/Zio-OLED-Display-0-91-in-128-32-Qwiic.html
Library: https://github.com/ZIOCC/Qwiic_TOF_Module_RFD77402/tree/master/micropython
"""

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

