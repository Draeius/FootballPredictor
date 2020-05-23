
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelBinarizer
from tensorflow.keras.layers import Dense
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import SGD

import numpy as np
import matplotlib.pyplot as plt

import pickle
import data

INIT_LR = 0.01
EPOCHS = 80

dc = data.DataComposer()
season = dc.getData(range(15, 19))

stopAt = round(len(season["matches"])*0.8)

trainX = season["matches"][:stopAt]
trainY = season["results"][:stopAt]

testX = season["matches"][stopAt:]
testY = season["results"][stopAt:]

inputVectorSize = len(trainX[0])

lb = LabelBinarizer()
trainY = lb.fit_transform(trainY)
testY = lb.transform(testY)

model = Sequential()
model.add(Dense(round(inputVectorSize*4), input_shape=(inputVectorSize,), activation="sigmoid"))
model.add(Dense(round(inputVectorSize), activation="sigmoid"))
model.add(Dense(len(lb.classes_), activation="softmax"))

print("[INFO] training network...")
opt = SGD(lr=INIT_LR)
model.compile(loss="categorical_crossentropy", optimizer=opt,
	metrics=["accuracy"])

H = model.fit(x=trainX, y=trainY, validation_data=(testX, testY),
	epochs=EPOCHS, batch_size=64)

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
plt.savefig("training.png")

print("[INFO] serializing network and label binarizer...")
model.save("data/keras.model", save_format="h5")
f = open("data/label.pickle", "wb")
f.write(pickle.dumps(lb))
f.close()