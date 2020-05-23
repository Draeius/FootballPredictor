
import pickle
from tensorflow.keras.models import load_model

#TODO: find some data

# load the model and label binarizer
print("[INFO] loading network and label binarizer...")
model = load_model("data/keras.model")
lb = pickle.loads(open("data/label.pickle", "rb").read())
# make a prediction on the data
preds = model.predict(data)
# find the class label index with the largest corresponding
# probability
i = preds.argmax(axis=1)[0]
label = lb.classes_[i]

# draw the class label + probability on the output image
text = "{}: {:.2f}%".format(label, preds[0][i] * 100)
print(text)