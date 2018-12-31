# Connects to Arduino via USB serial and writes characters to serial port
# Gordan Savicic, 25.5.2018

import serial

# change this to your serial port interface!!
ser = serial.Serial('/dev/ttyUSB0', 115200) # Establish the connection on a specific port


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
