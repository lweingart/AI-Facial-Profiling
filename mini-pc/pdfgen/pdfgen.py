# -*- coding: utf-8 -*-
import os
from io import BytesIO
from PyPDF2 import PdfFileWriter, PdfFileReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A5
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from yoctopuce.yocto_digitalio import *
from threading import Thread
import cups
import time
import socket
import logging
import os
import dmx
# beware, pip3 install pySerial, not just serial, which is something else


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('PDF generator')

current_time_in_seconds = lambda: int(round(time.time()*1000))


class Pdfgen:
    def __init__(self, image, label, score, template, destination, count, font, dmx, belt_running):
        # some attributes
        log.debug('Instantiating PdfGen object...')
        self.image = image
        self.score = '{0:.2f}'.format(float(score) * 100)
        self.template = template
        self.destination = destination
        self.count = count
        self.label = label
        self.dmx = dmx
        self.belt_running = belt_running
        self.yocto_name = 'YMINIIO0-D60E9'

        # some constants
        self.HIGH_STMP_WAIT_TIME = 5.25
        self.LOW_STMP_WAIT_TIME = 4.5
        self.STAMP_TO_BLOW_TIME = 2.3
        self.BELT_RUNNING_TIMEOUT = 5

        self.CLASSES = {
            'armed':'Firearms Shooting Skills',
            'unarmed': 'No Firearms Shooting Skills'
        }

        # some constants
        self.IMG_POS_X = 14
        self.IMG_POS_Y = 45
        self.IMG_SIZE = 277

        self.NUM_POS_X = 22
        self.NUM_POS_Y = 342
        self.FONT_SIZE = 11

        self.SCORE_POS_X = 315
        self.SCORE_POS_Y = 308

        self.CLASS_POS_X = 315
        self.CLASS_POS_Y = 342

        self.DATE_POS_X = 22
        self.DATE_POS_Y = 19

        self.PS_FONT_NAME = 'SuisseIntl-Regular'
        pdfmetrics.registerFont(TTFont(self.PS_FONT_NAME, font))

        if not os.path.isdir(self.destination):
            os.makedirs(self.destination)

        log.debug('PdfGen object instantiated')
        self._gen_pdf()


    def print(self, printer=None):
        conn = cups.Connection()
        default_printer = printer if not printer == None else 'HLL2350DW'
        printers = conn.getPrinters()
        if default_printer not in list(printers.keys()):
            raise PrinterError('Pdfgen.print()', "Could not find selected printer")
        pdf_file = '{}/{}.pdf'.format(self.destination, self.score)
        id = conn.printFile(default_printer, pdf_file, '', {'PageSize': 'A5', 'InputSlot': 'Rear', 'orientation-requested': '4'})
        # id = conn.printFile(default_printer, pdf_file, '', {'PageSize': 'A5', 'orientation-requested': '4', 'ColorModel': 'Gray'})
        start = current_time_in_seconds()

        # os.system('/usr/bin/lpr -P HLL2350DW ~/levels_of_paranoia/{}/{} -o media=a5 -o orientation-requested=4'.format(self.destination, self.score))
        t = Thread(target=self.read_sensor, args=(self.yocto_name,))
        log.debug('Yocto thread about to start...')
        t.start()

    def _gen_pdf(self):
        if self.count < 10: num = '0000{}'.format(self.count)
        elif self.count < 100: num = '000{}'.format(self.count)
        elif self.count < 1000: num = '00{}'.format(self.count)
        elif self.count < 10000: num = '0{}'.format(self.count)
        else : num = '{}'.format(self.count)

        num = 'WS - {}'.format(num)
        today = time.strftime('%a %b %d %Y %H:%M:%S')
        date = 'London, {}'.format(today)

        imgTemp = BytesIO()
        imgdoc = canvas.Canvas(imgTemp, pagesize=A5)
        imgdoc.drawImage(self.image, self.IMG_POS_X, self.IMG_POS_Y, self.IMG_SIZE, self.IMG_SIZE, preserveAspectRatio=True)
        imgdoc.setFont(self.PS_FONT_NAME, self.FONT_SIZE)
        imgdoc.drawString(self.NUM_POS_X, self.NUM_POS_Y, num)
        imgdoc.drawString(self.SCORE_POS_X, self.SCORE_POS_Y, self.score)
        imgdoc.drawString(self.DATE_POS_X, self.DATE_POS_Y, date)
        imgdoc.drawString(self.CLASS_POS_X, self.CLASS_POS_Y, self.CLASSES[self.label.lower()])
        imgdoc.save()

        # erase image file from system
        os.remove(self.image)

        img_pdf = PdfFileReader(BytesIO(imgTemp.getvalue())).getPage(0)
        img_pdf.rotateClockwise(90)
        base = PdfFileReader(open(self.template, 'rb')).getPage(0)
        base.rotateClockwise(90)
        base.mergePage(img_pdf)

        pdf = PdfFileWriter()
        pdf.addPage(base)
        pdf.write(open('{}/{}.pdf'.format(self.destination, self.score), 'wb'))
        # self._rotate_pdf()

    def read_sensor(self, sensor_id):
        log.debug('yocto thread started')
        def die(msg):
            sys.exit(msg + ' (check USB cable)')
        target = sensor_id.upper()
        errmsg = YRefParam()
        if YAPI.RegisterHub("usb", errmsg) != YAPI.SUCCESS:
            sys.exit("init error" + errmsg.value)

        if target == 'ANY':
            # retrieve any Relay then find its serial #
            io = YDigitalIO.FirstDigitalIO()
            if io is None:
                die('No module connected')
            m = io.get_module()
            target = m.get_serialNumber()

        log.info('using ' + target)
        io = YDigitalIO.FindDigitalIO(target + '.digitalIO')
        if not (io.isOnline()):
            die('device not connected')

        io.set_portDirection(0x00)  # all channels as inputs
        io.set_portPolarity(0)  # polarity set to regular
        io.set_portOpenDrain(1)  # Open drain

        loop = True
        log.info('::SENSOR:read_sensor(): inputdata = {}'.format(io.get_portState()))
        while loop:
            inputdata = io.get_portState()  # read port values
            # log.info('inputdata = {}'.format(inputdata))
            YAPI.Sleep(30)
            if inputdata == 0:
                log.info('::SENSOR:read_sensor(): inputdata = {}'.format(io.get_portState()))
                while io.get_portState() == 0:
                    pass
                log.info('Printing completed')
                if self.label.upper() == 'ARMED':
                    log.info('start chrono to stamp high')
                    time.sleep(self.HIGH_STMP_WAIT_TIME)
                    self.dmx.stamp_high()
                    time.sleep(self.STAMP_TO_BLOW_TIME)
                    self.dmx.blow()
                else:
                    log.info('start chrono to stamp low')
                    time.sleep(self.LOW_STMP_WAIT_TIME)
                    self.dmx.stamp_low()
                time.sleep(self.BELT_RUNNING_TIMEOUT)
                log.debug('belt count = {}'.format(len(self.belt_running)))
                if self.belt_running:
                    self.belt_running.pop()
                    # if not self.belt_running:
                        # self.dmx.belt_off()
                log.debug('belt count = {}'.format(len(self.belt_running)))
                loop = 0


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class PrinterError(Error):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message
