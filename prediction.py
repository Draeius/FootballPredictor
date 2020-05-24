
import pickle

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelBinarizer
from tensorflow.keras.layers import Dense, Dropout, Flatten
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.optimizers import SGD

import data


class Model:

    def __init__(self, learningRate: float, epochs: int, batchSize=16, dataSplit=.8):
        self.__learningRate = learningRate
        self.__epochs = epochs
        self.__model = None
        self.__dataSplit = dataSplit
        self.__batchSize = batchSize
        self.__history = None
        self.__labelBinarizer = LabelBinarizer()

    def __buildModel(self, data):
        print("[INFO] building network")
        self.__model = Sequential()
        self.__model.add(Dense(12, input_shape=self.getDataShape(data), activation="sigmoid"))
        self.__model.add(Dropout(.2))
        self.__model.add(Flatten())
        self.__model.add(Dense(6, activation="sigmoid"))
        self.__model.add(Dropout(.2))
        self.__model.add(Dense(len(self.__labelBinarizer.classes_), activation="softmax"))
        #self.__model = Sequential()
        #self.__model.add(Dense(40, input_shape=self.getDataShape(data), activation="sigmoid"))
        #self.__model.add(Dropout(.4))
        #self.__model.add(Flatten())
        #self.__model.add(Dense(22, activation="sigmoid"))
        #self.__model.add(Dropout(.3))
        #self.__model.add(Dense(8, activation="sigmoid"))
        #self.__model.add(Dropout(.2))
        #self.__model.add(Dense(len(self.__labelBinarizer.classes_), activation="softmax"))

        opt = SGD(lr=self.__learningRate)
        self.__model.compile(loss="categorical_crossentropy", optimizer=opt, metrics=["accuracy"])

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
            "trainX": np.asarray(data["matches"][:splitAt]).astype(np.int32),
            "trainY": data["results"][:splitAt],
            "testX": np.asarray(data["matches"][splitAt:]).astype(np.int32),
            "testY": data["results"][splitAt:]
        }

    def trainNewModel(self):
        dataSet = self.splitData(self.getTrainingData())

        trainY = self.__labelBinarizer.fit_transform(dataSet["trainY"])
        testY = self.__labelBinarizer.transform(dataSet["testY"])

        self.__buildModel(dataSet["trainX"])
        self.__history = self.__model.fit(x=dataSet["trainX"], y=trainY, validation_data=(dataSet["testX"], testY),
                                          epochs=self.__epochs, batch_size=self.__batchSize, verbose=1)

    def plotModel(self, fileDir):
        N = np.arange(0, self.__epochs)
        plt.style.use("ggplot")
        plt.figure()
        plt.plot(N, self.__history.history["loss"], label="train_loss")
        plt.plot(N, self.__history.history["val_loss"], label="val_loss")
        plt.plot(N, self.__history.history["accuracy"], label="train_acc")
        plt.plot(N, self.__history.history["val_accuracy"], label="val_acc")
        plt.title("Training Loss and Accuracy (Simple NN)")
        plt.xlabel("Epoch #")
        plt.ylabel("Loss/Accuracy")
        plt.legend()
        plt.savefig(fileDir + "training.png")

    def save(self, fileDir):
        print("[INFO] serializing network and label binarizer...")
        self.__model.save(fileDir + "keras.model", save_format="h5")
        f = open(fileDir + "label.pickle", "wb")
        f.write(pickle.dumps(self.__labelBinarizer))
        f.close()

    def load(self, fileDir):
        # load the model and label binarizer
        print("[INFO] loading network and label binarizer...")
        self.__model = load_model(fileDir + "keras.model")
        self.__labelBinarizer = pickle.loads(open(fileDir + "label.pickle", "rb").read())

    def predict(self):
        dataSet = self.getPredictData()
        dataSet["matches"] = np.asarray(dataSet["matches"]).astype(np.int32)
        truePreds = 0
        falsePreds = 0
        # make a prediction on the data
        preds = self.__model.predict(dataSet["matches"])
        # find the class label index with the largest corresponding probability
        
        argmax = preds.argmax(axis=1)
        for index in range(len(preds)):
            label = self.__labelBinarizer.classes_[argmax[index]]

            # draw the class label + probability on the output image
            text = "{}: {:.2f}% -- {} ;".format(label, preds[index][argmax[index]] * 100, str(label == dataSet["results"][index]))
            if label == dataSet["results"][index]:
                truePreds += 1
            else:
                falsePreds += 1

            print("[INFO] " + text)

        print("{:.2f}% correct".format(truePreds / (truePreds+falsePreds)))