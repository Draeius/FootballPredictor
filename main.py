from model import MatrixModel


model = MatrixModel(0.05, 400)
model.trainNewModel()

#model.load("data/currentBest/")


model.predict()
model.plotModel("data/output/")
model.save("data/output/")