
from sklearn.model_selection import GridSearchCV
from sklearn.neural_network import MLPClassifier
import data

dc = data.DataComposer(False)
season = dc.getData(range(15, 20))

matches = season["matches"]
results = season["results"]

stopAt = round(len(matches)*0.8)

gsc = GridSearchCV(
    estimator=MLPClassifier(),
    param_grid=[{
        'max_iter': [80, 90, 100, 110, 120, 250, 500],
        'solver': ['adam', 'sgd', 'lbfgs'],
        'alpha': [1e-5, 1e-4, 1e-3, 1e-2, 1e-2, 1e-1, 1, 10, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 1000],
        'hidden_layer_sizes': [(32, 16, 8), (16, 8), (12, 6), (8, 4), (6, 3), (4, 3)]
    }],
    cv=5, scoring=None, verbose=5, n_jobs=9)

gridResult = gsc.fit(matches[0:stopAt], results[0:stopAt])

print(gridResult.best_params_)
