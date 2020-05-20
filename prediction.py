from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, recall_score, precision_score
import data

dc = data.DataComposer()
season = dc.getData(range(15, 19))

matches = season["matches"]
results = season["results"]

stopAt = round(len(matches)*0.8)

clf = MLPClassifier(solver='adam', alpha=10, hidden_layer_sizes=(16, 8), random_state=1, max_iter=250)

clf.fit(matches[0:stopAt], results[0:stopAt])

#------------------------------------------------------------------------------
# get neural network scores
predicted = clf.predict(matches[stopAt:len(matches)])
correct = results[stopAt:len(matches)]

accuracy = accuracy_score(correct, predicted)
recall = recall_score(correct, predicted, average='macro')
precision = precision_score(correct, predicted, average='macro')
        
wRecall = recall_score(correct, predicted, average='weighted')
wPrecision = precision_score(correct, predicted, average='weighted')
#------------------------------------------------------------------------------

print(
    "######################################################################"
)

print("Accuracy: " + str(accuracy))
print("Recall: " + str(recall))
print("Precision: " + str(precision))
print("Weighted recall: " + str(wRecall))
print("Weighted precision: " + str(wPrecision))
