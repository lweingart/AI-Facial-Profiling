# Main program file for mini PC atchum
from PIL import Image, ImageDraw, ImageFont
from keras.applications.vgg19 import VGG19
from keras.preprocessing.image import img_to_array
from keras import Model
from sklearn.externals import joblib
import face_recognition as fr
import signal
import dmx
import numpy as np
import configparser
import pdfgen
import logging
import cv2
import random
import zmq
import base64
import os
import sys
import time


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('Main')


class Program:
    def __init__(self):
        # Read config file and set values
        config = configparser.ConfigParser()
        config.read('config.cfg')
        piface_ip = config.get('STREAM', 'piface_ip')
        piface_stream_port = config.get('STREAM', 'piface_stream_port')
        self.counter = config.getint('COUNTER_SECTION', 'counter')
        self.template = config.get('PDF', 'template')
        self.pdf_dir = config.get('PDF', 'dir')
        self.printer = config.get('PDF', 'printer')
        self.pdf_font = config.get('PDF', 'font_path')
        self.stream_url = config.get('STREAM', 'stream_url')
        self.font_size = config.getint('PIL_VALUES', 'font_size')
        self.font_name = config.get('PIL_VALUES', 'font_name')
        self.label = config.get('PIL_VALUES', 'label')
        # set a counter for the number of 'belt ON' signals
        self.belt_running = []
        # Load trained neural network
        fullVGG = VGG19()
        # remove last layer of the VGG model
        self.vgg = Model(inputs=fullVGG.input,
                    outputs=fullVGG.layers[24].output)
        self.classifier = joblib.load(config.get('ML', 'model'))
        # Prepare DMX constant value
        self.ON = 0xFF
        self.OFF = 0x00
        # Init DMX stuff
        self.dmx = dmx.DmxMsg('/dev/ttyUSB0')
        # Init network connection to send pictures back to raspi
        context = zmq.Context()
        self.footage_socket = context.socket(zmq.PUB)
        self.footage_socket.connect('tcp://' + piface_ip + ':' + piface_stream_port)

    def get_features(self, img):
        image = cv2.imread(img)
        image = cv2.resize(image, (224, 224))
        image = image.astype("float") / 255.0
        image = img_to_array(image)
        image = np.expand_dims(image, axis=0)
        layer_output = self.vgg.predict(image)
        return layer_output[0].reshape(1, -1)

    def detect_blur(self, image):
        return cv2.Laplacian(image, cv2.CV_64F).var()

    def resize_frame(self, frame, left, right, top, bottom):
        height = bottom - top
        width = right - left

        must_widen = width < height

        frame_height, frame_width, _ = frame.shape

        if must_widen:
            desired_width = height
            delta = desired_width - width
            adding = delta / 2
            left = int(left - adding)
            right = int(right + adding)
        else:
            desired_height = width
            delta = desired_height - height
            adding = delta / 2
            top = int(top - adding)
            bottom = int(bottom + adding)

        h_margin = round(width / 5)
        v_margin = h_margin

        top_crop = int(top) - int(v_margin)
        bottom_crop = int(bottom) + int(v_margin)
        left_crop = int(left) - int(h_margin)
        right_crop = int(right) + int(h_margin)

        if top_crop < 0:
            bottom_crop -= top_crop
            top_crop = 0
            if bottom_crop > frame_height:
                bottom_crop = frame_height
        if left_crop < 0:
            right_crop -= left_crop
            left_crop = 0
            if right_crop > frame_width:
                right_crop = frame_width
        if bottom_crop > frame_height:
            delta = bottom_crop - frame_height
            top_crop -= delta
            bottom_crop = frame_height
            if top_crop < 0:
                top_crop = 0
        if right_crop > frame_width:
            delta = right_crop - frame_width
            left_crop -= delta
            right_crop = frame_width
            if left_crop < 0:
                left_crop = 0
        return top_crop, bottom_crop, left_crop, right_crop

    def capture_face_picture(self, frame, left, right, top, bottom):
        os.system('/usr/bin/play sound/beep.wav')
        self.dmx.belt_on()
        self.belt_running.append('x')

        top_crop, bottom_crop, left_crop, right_crop = self.resize_frame(frame, left, right, top, bottom)
        result_image = frame[top_crop:bottom_crop, left_crop:right_crop]
        filename = 'pdfgen/images/face_{}.jpg'.format(str(random.random()))
        cv2.imwrite(filename, result_image)
        # cv2.cvtColor(result_image, cv2.COLOR_BGR2GRAY))

        features = self.get_features(filename)
        label = self.classifier.predict(features)
        probas = self.classifier.predict_proba(features)
        # print('label = {}'.format(label[0].toupper()))
        # print('label type is {}'.format(type(label)))
        proba = max(probas[0][0], probas[0][1])
        # print('proba = {}'.format(proba))
        print('')
        log.info('prediction: {} with proba {:.2f}'.format(str(label[0]).upper(), (float(proba) * 100)))
        print('')
        result = label[0]
        if label[0] == 'armed' and proba < 0.8:
            result = 'unarmed'

        self.generate_pdf(filename, result, proba)

    def generate_pdf(self, frame, label, proba):
        self.counter += 1
        pdf_gen = pdfgen.Pdfgen(frame, label, proba, self.template, self.pdf_dir,
                                self.counter, self.pdf_font, self.dmx, self.belt_running)
        pdf_gen.print(printer=self.printer)

    def stream_back(self, frame):
        _, buffer = cv2.imencode('.jpg', frame)
        img_str = base64.b64encode(buffer)
        self.footage_socket.send(img_str)

    def start(self):
        SQUARE_MARGIN = 20
        DELTA = 16
        SHARPNESS_THRESHOLD = 5
        RED = (255, 0, 0)
        GREEN = (0, 255, 0)
        WHITE = (255, 255, 255)
        FONT = ImageFont.truetype(self.font_name, self.font_size)
        stream = cv2.VideoCapture(self.stream_url)
        process_frame = True
        count = 0
        try:
            while True:
                # Grab a single frame of video
                ret, frame = stream.read()
                frame_clone = frame.copy()
                # log.debug('frame size = {}'.format(frame.shape))
                # Only process every other frame of video to save time
                # process_frame = not process_frame
                if process_frame:
                    # Resize frame of video to 1/4 size for faster face recognition processing
                    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

                    # Find all the faces and face encodings in the current frame of video
                    face_locations = fr.face_locations(small_frame, model="cnn")

                    # Display the results
                    if len(face_locations) > 0:
                        top, right, bottom, left = face_locations[0]
                        # Scale back up face locations since the frame we detected in was
                        # scaled to 1/2 size
                        left *= 4
                        left -= SQUARE_MARGIN
                        right *= 4
                        right += SQUARE_MARGIN
                        top *= 4
                        top -= SQUARE_MARGIN
                        bottom *= 4
                        bottom += SQUARE_MARGIN

                        width = right - left

                        # If the face is close enough to the camera to fill a certain
                        # portion of the screen
                        if width > 240:
                            count += 1
                            # change tp PIL format to draw and write on the image with
                            # more freedom
                            pil_image = Image.fromarray(frame[:, :, ::-1])
                            draw = ImageDraw.Draw(pil_image)
                            # draw 6 squares to get a thicker line
                            for i in range(0, 6):
                                draw.rectangle(((left - i, top - i), (right + i, bottom + i)), outline=RED)
                            draw.rectangle(((left, top), (right, top + self.font_size + 4)), fill=RED)
                            draw.text((left + 4, top + 1), self.label, WHITE, font=FONT)
                            frame_clone = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

                            sharpness = self.detect_blur(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
                            log.debug('sharpness of image: %s' % sharpness)

                            if sharpness > SHARPNESS_THRESHOLD and count > DELTA:
                                log.debug('count is %s and picture should be sent' % count)
                                # draw 6 squares to get a thicker line
                                for i in range(0, 6):
                                    draw.rectangle(((left - i, top - i), (right + i, bottom + i)), outline=GREEN)
                                draw.rectangle(((left - 5, top - 5), (right + 5, top + self.font_size + 4 + 5)), fill=GREEN)
                                draw.text((left + 4, top + 1), 'Analysing...', WHITE, font=FONT)
                                frame_clone = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

                                self.capture_face_picture(frame, left, right, top, bottom)

                                # send the same image for 32 frames (2 seconds)
                                for i in range(0, 32):
                                    print('same image x {}'.format(i + 1))
                                    self.stream_back(frame_clone)
                                    time.sleep(0.1)
                                count = 0
                        else:
                            if count > 0:
                                count = 0
                    else:
                        count = 0

                # Display the resulting image
                # cv2.imshow('Video', frame_clone)

                self.stream_back(frame_clone)

                # needed to display the video image
                # if cv2.waitKey(1) & 0xFF == ord('q'):
                #     break
        except KeyboardInterrupt:
            # Release handle to the webcam
            stream.release()
            cv2.destroyAllWindows()

    def signal_handler(self, sig, frame):
        log.debug('Keyboard interrupt exception caught !')
        db = configparser.ConfigParser()
        db.read('config.cfg')
        db.set('COUNTER_SECTION', 'counter', str(self.counter))
        with open('config.cfg', 'w') as conf:
            db.write(conf)
        self.dmx.belt_off()
        exit(0)


def main():
    prog = Program()
    signal.signal(signal.SIGINT, prog.signal_handler)
    try:
        prog.start()
    except Exception as e:
        log.error('Exception: {}'.format(e))
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        db = configparser.ConfigParser()
        db.read('config.cfg')
        db.set('COUNTER_SECTION', 'counter', str(prog.counter))
        with open('config.cfg', 'w') as conf:
            db.write(conf)
        prog.dmx.belt_off()


if __name__ == '__main__':
    main()
