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
        time.sleep(1)
        self.__blow = self.__OFF
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


