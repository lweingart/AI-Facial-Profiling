from keras.applications.vgg19 import VGG19
from keras.preprocessing.image import img_to_array
from keras import Model
from sklearn.externals import joblib
import cv2
import sys
import os
import numpy as np
np.set_printoptions(threshold=np.nan)


def get_features(vgg, img):
    image = cv2.imread(img)
    image = cv2.resize(image, (224, 224))
    image = image.astype("float") / 255.0
    image = img_to_array(image)
    image = np.expand_dims(image, axis=0)
    layer_output = vgg.predict(image)
    return layer_output[0].reshape(1, -1)


def perform_prediction(vgg, model, pic):
    features = get_features(vgg, pic)
    pred = model.predict(features)
    proba = model.predict_proba(features)
    print('Picture {}:'.format(pic))
    print('prediction is {}'.format(pred))
    print('probabilities are {}'.format(proba[0]))


def main(model, path):
    fullVGG = VGG19()
    classifier = joblib.load(model)

    # remove last layer of the VGG model
    vgg = Model(inputs=fullVGG.input,
                outputs=fullVGG.layers[24].output)

    files = []
    if os.path.isdir(path):
        for (dir, _, filenames) in os.walk(path):
            for f in filenames:
                if f.lower().endswith('.jpg'):
                    files.append(os.path.join(dir, f))
    else:
        files.append(path)

    for pic in files:
        perform_prediction(vgg, classifier, pic)


if __name__ == '__main__':
    model = sys.argv[1]
    path = sys.argv[2]
    main(model, path)
