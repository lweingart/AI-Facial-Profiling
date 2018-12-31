# Connects to Arduino via USB serial and writes characters to serial port
# Gordan Savicic, 25.5.2018

import serial

# change this to your serial port interface!!
ser = serial.Serial('/dev/ttyUSB0', 115200) # Establish the connection on a specific port
#
import serial
import time

class DmxMsg:
    def __init__(self, serial_port):
        self.__serial_port = serial.Serial(serial_port)
        self.__belt = 0x00
        self.__high_stmp = 0x00
        self.__low_stmp = 0x00
        self.__blow = 0x00
        self.__ON = 0xFF
        self.__OFF = 0x00
    def belt_on(self):
        self.__belt = self.__ON
        self.send_msg()
    def belt_off(self):
        self.__belt = self.__OFF
        self.send_msg()
    def stamp_high(self):
        self.__high_stmp = self.__ON
        self.send_msg()
        time.sleep(0.1)
        self.__high_stmp = self.__OFF
        self.send_msg()
    def stamp_low(self):
        self.__low_stmp = self.__ON
        self.send_msg()
        time.sleep(0.1)
        self.__low_stmp = self.__OFF
        self.send_msg()
    def blow(self):
        self.__blow = self.__ON
        self.send_msg()
    def send_msg(self):
        self.__serial_port.write(serial.to_bytes(self.__get_msg()))
    def __get_msg(self):
        return [
            0x7E,
            0x06,
            0x05,
            0x00,
            0x00,
            self.__belt,
            self.__high_stmp,
            self.__low_stmp,
            self.__blow,
            0xE7
        ]

dmx = DmxMsg()
dmx.blow()


while True:

    # for python2 use "input = raw_input()"
    txt = '''Enter character
    1  -  start belt
    2  -  stamp HIGH
    3  -  stamp LOW
    4  -  blow short
    5  -  stop belt
    6  -  start blowing
    7  -  stop blowing
    '''
    sendChar = input(txt)
    print("sending char %s to serial" % sendChar)
    ser.write(str.encode(sendChar))
    # if sendChar == 1:
        # s = bytes.fromhex('0x7E 0x06 0x04 0x00 0x00 0xFF 0x00 0x00 0xE7')
        # ser.write(str.encode(sendChar))
