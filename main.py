from prediction import Model


model = Model(0.1, 150)
model.trainNewModel()

#model.load("data/currentBest/")


model.predict()
model.plotModel("data/output/")
model.save("data/output/")