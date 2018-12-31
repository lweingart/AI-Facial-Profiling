from keras.applications.vgg19 import VGG19
from keras.preprocessing.image import img_to_array
from keras import Model
from sklearn.linear_model import LogisticRegressionCV
from sklearn.linear_model import LassoCV
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from sklearn.externals import joblib
import numpy as np
np.set_printoptions(threshold=np.nan)
import cv2
import os
import sys
import random


def create_trainset(path, vgg):
    trainset = []
    files = []
    for (dir, _, filenames) in os.walk(path):
        for f in filenames:
            if f.lower().endswith('.jpg'):
                files.append(os.path.join(dir, f))
    random.shuffle(files)
    for f in files:
        print(f)
        image = cv2.imread(f)
        image = cv2.resize(image, (224, 224))
        image = image.astype("float") / 255.0
        image = img_to_array(image)
        image = np.expand_dims(image, axis=0)
        layer_output = vgg.predict(image)
        if f.split(os.path.sep)[-1].split('.')[0].startswith('armed'):
            trainset.append({'armed': list(layer_output[0])})
        else:
            trainset.append({'unarmed': list(layer_output[0])})
    random.shuffle(trainset)
    return trainset


def split_dataset(dataset):
    X_train = []
    Y_train = []
    X_test = []
    Y_test = []
    print('dataset length is {}'.format(len(dataset)))
    part = int(round(0.8 * len(dataset)))
    for d in dataset[:part]:
        X_train.append(list(d.values())[0])
        Y_train.append(list(d.keys())[0])
    for d in dataset[part:]:
        X_test.append(list(d.values())[0])
        Y_test.append(list(d.keys())[0])
    return X_train, Y_train, X_test, Y_test


def save_model(model, path):
    # save the model to disk
    filename = path
    joblib.dump(model, filename)


def main(path, dest):
    fullVGG = VGG19()
    # remove last layer of the VGG model
    vgg = Model(inputs=fullVGG.input, outputs=fullVGG.layers[24].output)
    svd = PCA(n_components=500)
    # svd = PCA()
    logistic = LogisticRegressionCV(cv=20, max_iter=2000, class_weight='balanced', n_jobs=-1, multi_class='ovr', random_state=42)
    # logistic = LogisticRegressionCV(cv=4, max_iter=1000, class_weight='balanced', n_jobs=-1, multi_class='ovr', random_state=42)
    # lasso = LassoCV(max_iter=5000, cv=20)
    # pipe = Pipeline(steps=[('pca', svd), ('lasso', lasso)])
    pipe = Pipeline(steps=[('pca', svd), ('LR', logistic)])

    trainset = create_trainset(path, vgg)
    print('trainset type after function is {}'.format(type(trainset)))
    (X_train, Y_train, X_test, Y_test) = split_dataset(trainset)

    pipe.fit(X_train, Y_train)
    # logistic.fit(X_train, Y_train)
    # lasso.fit(X_train, Y_train)

    save_model(pipe, dest)
    # save_model(logistic, dest)
    # save_model(lasso, dest)

    result = pipe.score(X_test, Y_test)
    # result = logistic.score(X_test, Y_test)
    # result = lasso.score(X_test, Y_test)
    print(result)


if __name__ == '__main__':
    dataset_path = sys.argv[1]
    model_path = sys.argv[2]
    main(dataset_path, model_path)
