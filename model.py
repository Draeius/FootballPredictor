
import pickle

import matplotlib.pyplot as plt
import numpy as np

from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelBinarizer
from tensorflow.keras.layers import Dense, Dropout, Flatten, Convolution2D, MaxPooling2D
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.optimizers import SGD
from keras.preprocessing.image import ImageDataGenerator

import data

class Model:

    def __init__(self, learningRate: float, epochs: int, batchSize=16, dataSplit=.8):
        self._learningRate = learningRate
        self._epochs = epochs
        self._dataSplit = dataSplit
        self._batchSize = batchSize
        self._history = None
        self._labelBinarizer = LabelBinarizer()
        self._model = None

    def save(self, fileDir):
        print("[INFO] serializing network and label binarizer...")
        self._model.save(fileDir + "keras.model", save_format="h5")
        f = open(fileDir + "label.pickle", "wb")
        f.write(pickle.dumps(self._labelBinarizer))
        f.close()

    def load(self, fileDir):
        # load the model and label binarizer
        print("[INFO] loading network and label binarizer...")
        self._model = load_model(fileDir + "keras.model")
        self._labelBinarizer = pickle.loads(open(fileDir + "label.pickle", "rb").read())

    def plotModel(self, fileDir):
        N = np.arange(0, self._epochs)
        plt.style.use("ggplot")
        plt.figure()
        plt.plot(N, self._history.history["loss"], label="train_loss")
        plt.plot(N, self._history.history["val_loss"], label="val_loss")
        plt.plot(N, self._history.history["accuracy"], label="train_acc")
        plt.plot(N, self._history.history["val_accuracy"], label="val_acc")
        plt.title("Training Loss and Accuracy (Simple NN)")
        plt.xlabel("Epoch #")
        plt.ylabel("Loss/Accuracy")
        plt.legend()
        plt.savefig(fileDir + "training.png")


class MatrixModel(Model):

    def _buildModel(self, data):
        print("[INFO] building network")
        self._model = Sequential()
        self._model.add(Dense(12, input_shape=self.getDataShape(data), activation="sigmoid"))
        self._model.add(Dropout(.2))
        self._model.add(Flatten())
        self._model.add(Dense(6, activation="sigmoid"))
        self._model.add(Dropout(.2))
        self._model.add(Dense(len(self._labelBinarizer.classes_), activation="softmax"))

        opt = SGD(lr=self._learningRate)
        self._model.compile(loss="categorical_crossentropy", optimizer=opt, metrics=["accuracy"])

    def getTrainingData(self):
        dc = data.DataComposer("data/matches/", includeOldStats=False, includeBench=False, balance=True)
        return dc.getData()

    def getPredictData(self):
        dc = data.DataComposer("data/matches/test/", includeOldStats=False, includeBench=False, balance=True)
        return dc.getData()

    def getDataShape(self, data):
        return (len(data[0]), len(data[0][0]))

    def splitData(self, data):
        splitAt = round(len(data["matches"])*0.8)
        return {
            "trainX": np.asarray(data["matches"][:splitAt], np.float32),
            "trainY": data["results"][:splitAt],
            "testX": np.asarray(data["matches"][splitAt:], np.float32),
            "testY": data["results"][splitAt:]
        }

    def trainNewModel(self):
        dataSet = self.splitData(self.getTrainingData())

        trainY = self._labelBinarizer.fit_transform(dataSet["trainY"])
        testY = self._labelBinarizer.transform(dataSet["testY"])

        self._buildModel(dataSet["trainX"])
        self._history = self._model.fit(x=dataSet["trainX"], y=trainY, validation_data=(dataSet["testX"], testY),
                                          epochs=self._epochs, batch_size=self._batchSize, verbose=1)

    def predict(self):
        dataSet = self.getPredictData()
        dataSet["matches"] = np.asarray(dataSet["matches"], np.float32)
        truePreds = 0
        falsePreds = 0
        # make a prediction on the data
        preds = self._model.predict(dataSet["matches"])
        # find the class label index with the largest corresponding probability
        
        argmax = preds.argmax(axis=1)
        for index in range(len(preds)):
            label = self._labelBinarizer.classes_[argmax[index]]

            # draw the class label + probability on the output image
            text = "{}: {:.2f}% -- {} ;".format(label, preds[index][argmax[index]] * 100, str(label == dataSet["results"][index]))
            print(label, dataSet["results"][index])
            if label == dataSet["results"][index]:
                truePreds += 1
            else:
                falsePreds += 1

            print("[INFO] " + text)

        print("{:.2f}% correct".format(truePreds / (truePreds+falsePreds)))

    
class ImageModel(Model):

    def __init__(self, learningRate: float, epochs: int, batchSize=16, dataSplit=.8):
        super().__init__(learningRate, epochs, batchSize, dataSplit)
        self._dataGen = ImageDataGenerator(validation_split=dataSplit)

    def __buildModel(self):
        print("[INFO] building network")
        self._model = Sequential()
        #self._model.add(Convolution2D(32, 128, 96, activation="relu"))
        #self._model.add(Convolution2D(32, 128, 96, input_shape=(640, 480, 3), activation="relu"))
        #self._model.add(MaxPooling2D(pool_size=(4,3)))
        self._model.add(Flatten())
        self._model.add(Dense(66, activation="sigmoid"))
        self._model.add(Dense(22, activation="sigmoid"))
        self._model.add(Dense(3, activation="softmax"))

        opt = SGD(lr=self._learningRate)
        self._model.compile(loss="categorical_crossentropy", optimizer=opt, metrics=["accuracy"])

    def trainNewModel(self):
        self.__buildModel()
        self._history = self._model.fit(self._dataGen.flow_from_directory("data/images/train", batch_size=self._batchSize))

    def predict(self):
        pass


class Clusterer:
    pass