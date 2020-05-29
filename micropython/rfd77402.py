'''
Auther: Alex Chu
Website: www.smart-prototyping.com
Email: shop@smart-prototyping.com
product link: https://www.smart-prototyping.com/Zio-TOF-Distance-Sensor-RFD77402.html
RFD77402 datasheet: https://www.smart-prototyping.com/image/data/NOA-RnD/101891%20TOF/RFD77402DatasheetRev1-8.pdf
#reference: https://github.com/sparkfun/SparkFun_RFD77402_Arduino_Library/tree/master/src
'''

from machine import Pin,I2C
import pyb

RFD77402_ICSR = 0x00
RFD77402_INTERRUPTS = 0x02
RFD77402_COMMAND = 0x04
RFD77402_DEVICE_STATUS = 0x06
RFD77402_RESULT = 0x08
RFD77402_RESULT_CONFIDENCE= 0x0A
RFD77402_CONFIGURE_A = 0x0C
RFD77402_CONFIGURE_B = 0x0E
RFD77402_HOST_TO_MCPU_MAILBOX = 0x10
RFD77402_MCPU_TO_HOST_MAILBOX = 0x12
RFD77402_CONFIGURE_PMU = 0x14
RFD77402_CONFIGURE_I2C = 0x1C
RFD77402_CONFIGURE_HW_0 = 0x20
RFD77402_CONFIGURE_HW_1 = 0x22
RFD77402_CONFIGURE_HW_2 = 0x24
RFD77402_CONFIGURE_HW_3 = 0x26
RFD77402_MOD_CHIP_ID = 0x28

RFD77402_MODE_MEASUREMENT = 0x01
RFD77402_MODE_STANDBY = 0x10
RFD77402_MODE_OFF = 0x11
RFD77402_MODE_ON = 0x12

CODE_VALID_DATA = 0x00
CODE_FAILED_PIXELS = 0x01
CODE_FAILED_SIGNAL = 0x02
CODE_FAILED_SATURATED = 0x03
CODE_FAILED_NOT_NEW = 0x04
CODE_FAILED_TIMEOUT = 0x05

I2C_SPEED_STANDARD = 100000
I2C_SPEED_FAST = 400000

INT_CLR_REG = 1 # tells which register read clears the interrupt (Default: 1, Result Register)
INT_CLR = 0 << 1 # tells whether or not to clear when register is read (Default: 0, cleared upon register read)
INT_PIN_TYPE = 1 << 2 # tells whether int is push-pull or open drain (Default: 1, push-pull)
INT_LOHI = 0 << 3 # tells whether the interrupt is active low or high (Default: 0, active low)

# Setting any of the following bits to 1 enables an interrupt when that event occurs
INTSRC_DATA = 1      # Interrupt fires with newly available data
INTSRC_M2H = 0 << 1  # Interrupt fires with newly available data in M2H mailbox register
INTSRC_H2M = 0 << 2  # Interrupt fires when H2M register is read
INTSRC_RST = 0 << 3  # Interrupt fires when HW reset occurs


class RFD77402:

    def __init__(self,addr,i2c):
        self.addr = 0x4C
        self.i2c = i2c
        self.distance = 0
        self.validPixels = 0
        self.confidenceValue = 0
        self.calibrationData =[]
        self.cmd_1_byte =bytearray(1)
        self.cmd_2_byte = bytearray(2)

    def begin(self):
        if self.getChipID() < 0xAD00:
            return False
        # Deivce power on flow, from datasheet page 29
        if self.goToStandbyMode() == False:
            return False
        # Drive INT_PAD high
        setting = self.i2c.readfrom_mem(self.addr, RFD77402_ICSR, 1)
        # clears writable bits
        setting_int = setting[0] & 0b11110000
        # change bits to enable interrupt
        setting_int |= INT_CLR_REG | INT_CLR | INT_PIN_TYPE | INT_LOHI
        self.cmd_1_byte[0] = setting_int
        print(self.cmd_1_byte)
        self.i2c.writeto_mem(self.addr, RFD77402_ICSR, self.cmd_1_byte)
        setting = self.i2c.readfrom_mem(self.addr, RFD77402_INTERRUPTS, 1)
        # Clears bits
        setting_int = setting[0] & 0b00000000
        # setting = 0b00000000
        setting_int |= INTSRC_DATA | INTSRC_M2H | INTSRC_H2M | INTSRC_RST
        self.cmd_1_byte[0] = setting_int
        # setting |= INTSRC_DATA | INTSRC_M2H | INTSRC_H2M | INTSRC_RST  # Enables interrupt when data is ready
        self.i2c.writeto_mem(self.addr, RFD77402_INTERRUPTS, self.cmd_1_byte) # 1 byte
        # Configure I2C Interface,
        # //0b.0110.0101 = 0x65 Address increment, auto increment, host debug, MCPU debug, 2.1.3 setting
        self.i2c.writeto_mem(self.addr, RFD77402_CONFIGURE_I2C, b'\x65')
        # //0b.0000.0101.0000.0000 //Patch_code_id_en, Patch_mem_en
        self.i2c.writeto_mem(self.addr, RFD77402_CONFIGURE_PMU, b'\x00\x05')  # 0x0500
        if self.goToOffMode() == False:
            return False
        # set initialization - Magic from datasheet. Write 0x0600 to 0x14 location
        self.i2c.writeto_mem(self.addr, RFD77402_CONFIGURE_PMU, b'\x00\x06') # 0x0600
        if self.goToOnMode() == False:
            return False
        # set peak and threshold 0xe100
        self.i2c.writeto_mem(self.addr, RFD77402_CONFIGURE_A, b'\x00\xe1')
        self.i2c.writeto_mem(self.addr, RFD77402_CONFIGURE_B, b'\xff\x10') # Set valid pixel. Set MSP430 default config. cmd: 0x10FF
        self.i2c.writeto_mem(self.addr, RFD77402_CONFIGURE_HW_0, b'\xd0\x07') # Set saturation threshold = 2,000.   cmd:0x07D0
        self.i2c.writeto_mem(self.addr, RFD77402_CONFIGURE_HW_1, b'\x08\x50') # Frequecy = 5. Low level threshold = 8, cmd: 0x5008
        self.i2c.writeto_mem(self.addr, RFD77402_CONFIGURE_HW_2, b'\x41\xa0') # cmd: 0xA041. Integration time = 10 * (6500-20)/15)+20 = 4.340ms. Plus reserved magic.
        self.i2c.writeto_mem(self.addr, RFD77402_CONFIGURE_HW_3, b'\xd4\x45') # cmd: 0x45D4. Enable harmonic cancellation. Enable auto adjust of integration time. Plus reserved magic.
        # Error - MCPU never went to standby
        if self.goToStandbyMode() == False:
            return False
        # Set initialization - Magic from datasheet. Write 0x05 to 0x15 location.
        self.i2c.writeto_mem(self.addr, RFD77402_CONFIGURE_PMU, b'\x00\x05')
        if self.goToOffMode() == False:
            return False
        # Set initialization - Magic from datasheet. Write 0x06 to 0x15 location.
        self.i2c.writeto_mem(self.addr, RFD77402_CONFIGURE_PMU, b'\x00\x06')
        if self.goToOnMode() == False:
            return False
        return True

    # Single Measure Flow, from datasheet page 30
    def takeMeasurement(self):
        if self.goToMeasurementMode() == False:
            return CODE_FAILED_TIMEOUT
        resultRegister = self.i2c.readfrom_mem(self.addr, RFD77402_RESULT,2)
        resultRegister_int = (resultRegister[1]<<8) | resultRegister[0]
        if resultRegister_int & 0x7FFF:
            errorCode = (resultRegister[1] >> 5) & 0x03
            if errorCode == 0:
                self.distance = ((resultRegister[1] & 0x1F) << 8) | resultRegister[0] # Distance is good. Read it.
                self.distance = self.distance >> 2
                confidenceRegister = self.i2c.readfrom_mem(self.addr, RFD77402_RESULT_CONFIDENCE, 2)
                confidenceRegister_int = (confidenceRegister[1] << 8) | confidenceRegister[0]
                self.validPixels = confidenceRegister_int & 0x0F
                self.confidenceValue = (confidenceRegister_int >> 4) & 0x07FF
            else:
                return errorCode
        else:
            return CODE_FAILED_NOT_NEW

    def getDistance(self):
        return self.distance

    def getValidPixels(self):
        return self.validPixels

    def getConfidenceValue(self):
        return self.confidenceValue

    def getMode(self):
        return (self.i2c.readfrom_mem(self.addr, RFD77402_COMMAND,1)[0] & 0x3F)

    def goToStandbyMode(self):
        self.i2c.writeto_mem(self.addr, RFD77402_COMMAND, b'\x90')
        mode_mark= False
        for i in range(0, 10):
            a = self.i2c.readfrom_mem(self.addr, RFD77402_DEVICE_STATUS, 2)
            if a[0] & 0x1F == 0x00:
                mode_mark = True
                return True
            pyb.delay(10)
        if mode_mark == False:
            return False

    def goToOffMode(self):
        # set MCPU_OFF
        self.i2c.writeto_mem(self.addr, RFD77402_COMMAND, b'\x91') #0b.1001.0001 = Go MCPU off state. Set valid command. 0x91
        # Check MCPU_OFF Status
        mode_mark = False
        for i in range(0,10):
            a = self.i2c.readfrom_mem(self.addr, RFD77402_DEVICE_STATUS, 2)
            if a[0] & 0x1F == 0x10:
                mode_mark = True
                return True
            pyb.delay(10)
        if mode_mark == False:
            return False

    def goToOnMode(self):
        # Set MCPU_ON
        self.i2c.writeto_mem(self.addr, RFD77402_COMMAND, b'\x92')
        mode_mark = False
        for i in range(0, 10):
            a = self.i2c.readfrom_mem(self.addr, RFD77402_DEVICE_STATUS, 2)
            if a[0] & 0x1F == 0x18:  # MCPU is now on
                mode_mark = True
                return True
            pyb.delay(10)
        if mode_mark == False:
            return False

    # Takes a measurement. If measurement data is ready, return true
    def goToMeasurementMode(self):
        # Single measure command
        # 0b.1000.0001 = Single measurement. Set valid command.
        self.i2c.writeto_mem(self.addr, RFD77402_COMMAND, b'\x81')
        mode_mark = False
        # Read ICSR Register - Check to see if measurement data is ready
        for i in range(0, 10):
            a = self.i2c.readfrom_mem(self.addr, RFD77402_ICSR, 1)
            if a[0] & (1<<4) != 0:  # Data is ready!
                mode_mark = True
                return True
            pyb.delay(10)
        if mode_mark == False:
            return False

    def getPeak(self):
        readpeak = self.i2c.readfrom_mem(self.addr, RFD77402_CONFIGURE_A, 2)
        peak_int = (readpeak[1] << 8) | readpeak[0]
        return (peak_int >>12) & 0x0F

    def setPeak(self, peakValue=0x0E):
        configValue  = self.i2c.readfrom_mem(self.addr, RFD77402_CONFIGURE_A,2)
        configValue_int = (configValue[1] << 8) | configValue[0]
        configValue_int &= ~0xF000
        configValue_int |= peakValue << 12
        # construct cmd bytearray
        self.cmd_2_byte[0] = configValue_int & 0xff
        self.cmd_2_byte[1] = configValue_int >> 8
        self.i2c.writeto_mem(self.addr, RFD77402_CONFIGURE_A, self.cmd_2_byte)

    # not tested, based on sparkfun's library
    def getThreshold(self):
        configValue = self.i2c.readfrom_mem(self.addr, RFD77402_CONFIGURE_A, 2)
        return configValue[1] & 0x0F

    # Sets the VCSEL Threshold 4-bit value
    def setThreshold(self,thresholdValue):
        configValue = self.i2c.readfrom_mem(self.addr, RFD77402_CONFIGURE_A, 2)
        configValue_int = (configValue[1] << 8) | configValue[0]
        configValue_int &= ~0xF000
        configValue_int |= thresholdValue << 8
        # construct cmd bytearray
        self.cmd_2_byte[0] = configValue_int & 0xff
        self.cmd_2_byte[1] = configValue_int >> 8
        self.i2c.writeto_mem(self.addr, RFD77402_CONFIGURE_A, self.cmd_2_byte)

    # Returns the VCSEL Frequency 4-bit value # not tested, based on sparkfun's library
    def getFrequency(self):
        readfre = self.i2c.readfrom_mem(self.addr, RFD77402_CONFIGURE_HW_1, 2)
        fre_int = (readfre[1] << 8) | readfre[0]
        return (fre_int >> 12) & 0x0F

    # Sets the VCSEL Frequency 4-bit value, not tested, based on sparkfun's library
    def setFrequency(self,thresholdValue):
        configValue = self.i2c.readfrom_mem(self.addr, RFD77402_CONFIGURE_HW_1,2)
        configValue_int = (configValue[1] << 8) | configValue[0]
        configValue_int &= ~0xF000
        configValue_int |= thresholdValue << 12
        # construct cmd bytearray
        self.cmd_2_byte[0] = configValue_int & 0xff
        self.cmd_2_byte[1] = configValue_int >> 8
        self.i2c.writeto_mem(self.addr, RFD77402_CONFIGURE_HW_1, self.cmd_2_byte)

    # not tested, based on sparkfun's library
    def getMailbox(self):
        mailbox = self.i2c.readfrom_mem(self.addr, RFD77402_MCPU_TO_HOST_MAILBOX, 2)
        mailbox_int = (mailbox[1] << 8) | mailbox[0]
        return mailbox_int

    def reset(self):
        self.i2c.writeto_mem(self.addr, RFD77402_COMMAND, b'x40') # 1<<6
        pyb.delay(10)

    # Should be 0xAD01 or higher
    def getChipID(self):
        chipid = self.i2c.readfrom_mem(self.addr, RFD77402_MOD_CHIP_ID, 2)
        id_int = (chipid[1] <<8) | chipid[0]
        return id_int

    def getCalibrationData(self):
        # not tested, based on sparkfun's library
        if self.goToOnMode() == False:
            return False
        # Check ICSR Register and read Mailbox until it is empty
        message = 0
        while (1):
            a_int = self.i2c.readfrom_mem(self.addr, RFD77402_ICSR,1)[0]
            if (a_int & (1 <<5)) == 0:
                break
            self.getMailbox()
            message +=1
            if message > 27:
                return False
        self.i2c.writeto_mem(self.addr, RFD77402_HOST_TO_MCPU_MAILBOX, b'\x00\x06') # 0x0006
        for i in range(0,27):
            x = 0
            while (1):
                iscr = self.i2c.readfrom_mem(self.addr, RFD77402_ICSR, 1)
                if iscr[0] & (1<<5) != 0:
                    break
                x +=1
                if x > 10:
                    return False
                pyb.delay(10)
            incoming = self.getMailbox()
            self.calibrationData[i*2] = incoming>>8
            self.calibrationData[i*2+1] = incoming & 0xFF
