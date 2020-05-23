
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelBinarizer
from tensorflow.keras.layers import Dense, Flatten, Dropout
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import SGD

import numpy as np
import matplotlib.pyplot as plt

import pickle
import data

INIT_LR = 0.02
EPOCHS = 2000

dc = data.DataComposer("data/matches/", includeOldStats=False, includeBench=False, balance=True)
season = dc.getData()

stopAt = round(len(season["matches"])*0.8)

trainX = np.asarray(season["matches"][:stopAt]).astype(np.int32)
trainY = season["results"][:stopAt]

testX = np.asarray(season["matches"][stopAt:]).astype(np.int32)
testY = season["results"][stopAt:]

matrixX = len(trainX[0])
matrixY = len(trainX[0][0])

lb = LabelBinarizer()
trainY = lb.fit_transform(trainY)
testY = lb.transform(testY)


print("[INFO] building network")
model = Sequential()
model.add(Dense(40, input_shape=(matrixX, matrixY,), activation="sigmoid"))
model.add(Dropout(.4))
model.add(Flatten())
#model.add(Dense(round(matrixX/6), activation="sigmoid"))
model.add(Dense(22, activation="sigmoid"))
model.add(Dropout(.3))
#model.add(Dense(round(matrixX/15), activation="sigmoid"))
model.add(Dense(8, activation="sigmoid"))
model.add(Dropout(.2))
model.add(Dense(len(lb.classes_), activation="softmax"))

print("[INFO] training network...")
opt = SGD(lr=INIT_LR)
model.compile(loss="categorical_crossentropy", optimizer=opt,
	metrics=["accuracy"])

H = model.fit(x=trainX, y=trainY, validation_data=(testX, testY),
	epochs=EPOCHS, batch_size=16)

# plot the training loss and accuracy
N = np.arange(0, EPOCHS)
plt.style.use("ggplot")
plt.figure()
plt.plot(N, H.history["loss"], label="train_loss")
plt.plot(N, H.history["val_loss"], label="val_loss")
plt.plot(N, H.history["accuracy"], label="train_acc")
plt.plot(N, H.history["val_accuracy"], label="val_acc")
plt.title("Training Loss and Accuracy (Simple NN)")
plt.xlabel("Epoch #")
plt.ylabel("Loss/Accuracy")
plt.legend()
plt.savefig("data/output/training.png")

print("[INFO] serializing network and label binarizer...")
model.save("data/output/keras.model", save_format="h5")
f = open("data/output/label.pickle", "wb")
f.write(pickle.dumps(lb))
f.close()