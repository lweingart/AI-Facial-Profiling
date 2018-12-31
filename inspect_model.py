# import the necessary packages
from keras.applications.vgg19 import VGG19
import argparse


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument('-i', '--include-top', type=int, default=1, help='whether or not to include top of CNN')
args = vars(ap.parse_args())
# load the VGG16 network
print('[INFO] loading network...')
model = VGG19(include_top=args['include_top'] > 0, weights='imagenet')
print('[INFO] showing layers...')
# loop over the layers in the network and display them to the
# console
for (i, layer) in enumerate(model.layers):
    print('[INFO] {}\t{}'.format(i, layer.__class__.__name__))
