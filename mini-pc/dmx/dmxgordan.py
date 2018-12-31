import serial
import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('DMX')

class DmxGordan:
    def __init__(self, serial_port):
        self.serial_port = serial.Serial(serial_port, 115200)
    def belt_on(self):
        log.info('start belt')
        self.send_msg('1')
    def belt_off(self):
        log.info('stop belt')
        self.send_msg('5')
    def stamp_high(self):
        log.info('stamp high')
        self.send_msg('2')
    def stamp_low(self):
        log.info('stamp low')
        self.send_msg('3')
    def blow(self):
        log.info('blow')
        self.send_msg('4')
    def send_msg(self, char):
        self.serial_port.write(str.encode(char))
