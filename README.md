# Qwiic_TOF_Module_RFD77402

https://www.smart-prototyping.com/Zio-TOF-Distance-Sensor-RFD77402.html

This is a great little TOF rangefinder module based on the RFD77402 which has a two-meter range.

Worth noting about this sensor is that it has a fixed I2C address, which means you'll need a <a href="https://www.smart-prototyping.com/Zio-Qwiic-Mux.html">multiplexer</a> or intermediate slave device like a sensor hub, if you want to connect more than one of them to the same bus.

For Arduino users, the best option is Sparkfun's library, to which we've linked from the product page listed above.

Note: As with all of the Version 1.0 Zio Qwiic boards, this board has been produced with the I2C pull-ups disconnected by default. If there's a significant length of wire between this board and your MCU, you'll need to solder closed the solder jumpers (labeled SDA, 3v3 and SCL) to connect the pull-up resistors to VCC.

All Zio products are released under the Creative Commons Attribution, Share-Alike License, and in accordance with the principles of the Open Source Hardware Association's OSHW Statement of Principles 1.0 and OSHW Definition 1.0. https://creativecommons.org/licenses/by-sa/4.0/ https://www.oshwa.org/definition/ https://www.oshwa.org/definition/chinese/
