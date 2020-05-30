
import json
import mapping
import glob
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

import os.path as path
from statistics import mean 
from sklearn import preprocessing


class DataComposer:

    WINNING_LABELS = ["Win A", "Draw", "Win B"]

    def __init__(self, directory: str, includeOldStats=True, includeBench=True, balance=False, scale = True):
        self.__includeBench = includeBench
        self.__includeOldStats = includeOldStats
        self.__balance = balance
        self.__fileLoader = FileLoader(directory)
        self.__scale = scale

    def __fixPosition(self, position):
        switcher = {
            1: 6,
            2: 7,
            3: 8,
            4: 9,
            5: 10,
            6: 11,
            7: 12,
            8: 13,
            9: 14,
            10: 15,
            12: 16,
            13: 17,
            14: 18,
            17: 19
        }
        return switcher[position]

    def getMatchWinner(self, score: str):
        arr = score.split("-")
        if arr[0] > arr[1]:
            return self.WINNING_LABELS[0]
        if arr[1] > arr[0]:
            return self.WINNING_LABELS[2]
        return self.WINNING_LABELS[1]

    def crateAvgPlayer(self, team):
        skill = [0]*34
        for index in range(34):
            totalSkill = 75
            members = 1
            for member in team:
                if "skill" in member.keys() and member["skill"] != None:
                    if type(member["skill"][1][index]) == type("") and "lbs" in member["skill"][1][index]:
                        totalSkill += 75
                    else:
                        totalSkill += int(member["skill"][1][index])
                        members += 1
            skill[index] = round(totalSkill / members)
        return skill

    def getPlayerSkill(self, team, player):
        if "skill" in player.keys() and player["skill"] != None:
            if type(player["skill"][1][0]) == type("") and "lbs" in player["skill"][1][0]:
                skill = player["skill"][1]
                del skill[0]
                skill.insert(11, 75)
                return skill

            return player["skill"][1]
        
        return self.crateAvgPlayer(team)

    def getTeam(self, team):
        if self.__includeBench:
            result = [[0]*34]*40
        else:
            result = [[0]*34]*20
        mapper = mapping.PositionMapper()
        benchPos = 20
        emptyPos = [0]*34
        for member in team:
            if member["position"] != None:
                try:
                    position = mapper.matchPosition([member["position"]["top"], member["position"]["left"]])
                except:
                    print("During player " + member["name"])
                    raise

                if result[position] != emptyPos and result[position] != self.getPlayerSkill(team, member):
                    # fix some issues with some formations
                    newPosition = self.__fixPosition(position)
                    if result[newPosition] != 0:
                        continue
                    position = newPosition
            elif self.__includeBench:
                position = benchPos
                benchPos += 1

            result[position] = self.getPlayerSkill(team, member)
        return result

    def parseMatch(self, match):
        result = {"match": [], "result": -1}
        for team in match["teams"]:
            result["match"] += self.getTeam(team)

        if self.__scale:
            result["match"] = np.divide(np.asarray(result["match"], dtype=np.float32), 100)
            
        result["result"] = self.getMatchWinner(match["score"])
        return result

    def getData(self):
        print("[INFO] Composing data")
        data = {"matches": [], "results": []}
        file = self.__fileLoader.getNextFile()
        while file:
            mData = json.load(file)
            skill = mData["teams"][0][0]["skill"]
            if skill and ("lbs" not in skill[1][0] or self.__includeOldStats):
                match = self.parseMatch(mData)
                data["matches"].append(match["match"])
                data["results"].append(match["result"])

            file = self.__fileLoader.getNextFile()
        
        #for index in range(len(data["matches"])):
        #    data["matches"][index] = preprocessing.scale(data["matches"][index])
        if self.__balance:
            return self.balance(data)
            
        return data

    def balance(self, data):
        matches = {"a": [], "b": [], "u": []}
        count = range(len(data["results"]))
        for index in count:
            if data["results"][index] == self.WINNING_LABELS[0]:
                matches["a"].append([data["matches"][index], data["results"][index]])
            elif data["results"][index] == self.WINNING_LABELS[1]:
                matches["u"].append([data["matches"][index], data["results"][index]])
            else:
                matches["b"].append([data["matches"][index], data["results"][index]])        

        maximum = max([len(matches["a"]), len(matches["b"]), len(matches["u"])])

        for winner in ["a", "b", "u"]:
            while len(matches[winner]) < maximum:
                random = np.random.randint(0, len(matches[winner]))
                matches[winner].append(matches[winner][random])

        ordered = []
        for winner in ["a", "b", "u"]:
            ordered += matches[winner]

        np.random.shuffle(ordered)

        matches = [match[0] for match in ordered]
        results = [match[1] for match in ordered]
    
        return {"matches": matches, "results": results}


class FileLoader:

    def __init__(self, directory: str, fileType = "txt"):
        # get all available files
        self.__filesNames = glob.glob(directory + "*." + fileType)
        # init current as 0
        self.__current = 0
        # save filecount to minimize runtime lateron
        self.__fileCount = len(self.__filesNames)

    def getNextFile(self):
        # check if there is still a file left
        if self.hasNextFile():
            # increase counter
            self.__current += 1
            # return next file
            return open(self.__filesNames[self.__current], "r")

        # no further files
        return None

    def hasNextFile(self) -> bool:
        return self.__current + 1 < self.__fileCount


class DataPlotter:

    def __init__(self, directory: str, outputDirectory: str):
        self.__fileLoader = FileLoader(directory)
        self.__directory = directory
        self.__outputDirectory = outputDirectory

    def __plotYDistribution(self, data):
        print("[INFO] Plotting Y distribution")
        dc = DataComposer(self.__directory, includeBench=False, includeOldStats=False, balance=True)
        # determine the winner of every match
        yData = [winner for winner in dc.getData()["results"]]
        # empty dict to save the result
        counts = {}
        # iterate possible outcomes
        for label in DataComposer.WINNING_LABELS:
            # count occurances of outcome in yData
            counts[label] = yData.count(label)

        # separate names and values
        names = list(counts.keys())
        values = list(counts.values())
        # plot
        plt.bar(names, values)
        # save image
        plt.savefig(self.__outputDirectory + "YDistribution.png")
        plt.clf()

    def __plotMissingPlayerSkill(self, data):
        print("[INFO] Plotting players missing skill")
        players = []
        for match in data:
            for team in match["teams"]:
                for pl in team:
                    if pl["skill"] == None:
                        players.append(0)
                    elif "lbs" in pl["skill"][1][0]:
                        players.append(1)
                    else:
                        players.append(2)

        names = ["Missing", "Not enough", "good"]
        values = [players.count(0), players.count(1), players.count(2)]
        percMissing = round(100 * values[0] / (values[0] + values[1] + values[2]), 2)
        percNEnough = round(100 * values[1] / (values[1] + values[2]), 2)
        plt.title("Missing skill: " + str(percMissing) + "%, not enough: " + str(percNEnough) + "%")
        # plot
        plt.bar(names, values)
        # save image
        plt.savefig(self.__outputDirectory + "MissingSkill.png")
        plt.clf()

    def plot(self):
        data = []
        file = self.__fileLoader.getNextFile()
        while file:
            data.append(json.load(file))
            file = self.__fileLoader.getNextFile()

        self.__plotYDistribution(data)
        self.__plotMissingPlayerSkill(data)


class ImagePrinter:

    def __init__(self):
        self.__dComp = DataComposer("")

    def __getColorBySkill(self, skill):
        mix = skill / 100
        red = np.array(mpl.colors.to_rgb("#ff0000"))
        green = np.array(mpl.colors.to_rgb("#00cc00"))
        return mpl.colors.to_hex((1 - mix) * red + mix * green)

    def __getPlayerAvg(self, skills):
        if not skills:
            return 50

        skills = skills[1]
        
        if "lbs" in skills[0]:
            avg = mean([int(value) for value in skills[1:-5]])
        else:
            avg = mean([int(value) for value in skills[:-5]])

        return avg

    def __getPlayerColor(self, player):
        if player["position"] == {"top": 50, "left": 5}:
            avg = mean([int(value) for value in player["skill"][1][-5:]])
        else:
            avg = self.__getPlayerAvg(player["skill"])
            
        return self.__getColorBySkill(avg)

    def __getWorkingRates(self, skill):
        switch = {
            "Niedrig": 1.5,
            "Mittel": 3,
            "Hoch": 4.5
        }
        if not skill:
            return [switch["Mittel"], switch["Mittel"]]

        workingRateStr = skill[0][3]
        rates = workingRateStr.split(" / ")
        rates[0] = switch[rates[0]]
        rates[1] = switch[rates[1]]
        return rates

    def __createImage(self, match, fileName, baseDir):
        pointsX = []
        pointsY = []
        colors = []
        for index in [0,1]:
            for member in match["teams"][index]:
                if member["position"]:
                    colors.append(self.__getPlayerColor(member))
                    Y = member["position"]["top"]
                    if index:
                        X = member["position"]["left"] - 7
                    else:
                        X = 107 - member["position"]["left"]
                    
                    pointsX.append(X)
                    pointsY.append(Y)
                    rates = self.__getWorkingRates(member["skill"])
                    plt.plot([X, X + rates[0]], [Y, Y], 'k-', lw=2)
                    plt.plot([X, X - rates[1]], [Y, Y], 'k-', lw=2)
        plt.scatter(pointsX, pointsY, c=colors)
        plt.axis('off')
        directory = self.__dComp.getMatchWinner(match["score"])
        plt.savefig(baseDir+directory+"/"+fileName+".png")
        plt.clf()


    def print(self):
        fl = FileLoader("data/matches/test/")
        match = fl.getNextFile()
        while match:
            fileName = path.basename(match.name.split(".")[0])
            try:
                self.__createImage(json.load(match), fileName, "data/images/test/")
            except TypeError:
                pass
            match = fl.getNextFile()

