
import json
import mapping
import glob
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

import os.path as path
from statistics import mean 
from sklearn import preprocessing


class Player:

    def __init__(self, name, data, position):
        self.position = position
        self.name = name
        self.misc = data
        self.skills = data[1]

    def __isOldData(self, data) -> bool:
        """
        Determines if the given data is from an older version of fifa
        """
        # if version is older, then there will be a string in the first index of the skills array
        return type(data[1][0]) == type("")

    @property
    def position(self):
        return self.__position

    @position.setter
    def position(self, position):
        self.__position = position

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, name):
        self.__name = name

    @property
    def misc(self):
        return self.__misc

    @misc.setter
    def misc(self, data):
        self.__misc = data[0]
        # check if data is from an older fifa version
        # older versions had one less attribute
        if type(data[1][0]) == type(""):
            # append the missing data to misc
            self.__misc.append(data[1][0])

    @property
    def skills(self):
        return self.__skills

    @skills.setter
    def skills(self, data):
        # check if data is from an older fifa version
        # older versions had one less attribute
        if type(data[0]) == type(""):
            # delete string where it is not meant to be
            del data[0]
            # add 75 as dummy
            data.insert(11, 75)
        
        self.__skills = np.asarray(data)


class Team:

    def __init__(self, data, includeBench):
        self.__includeBench = includeBench
        self.__grid = None
        self.members = data

    def __updateGrid(self):
        if self.__includeBench:
            self.__grid = np.zeros((40,34))
        else:
            self.__grid = np.zeros((20,34))
        
        benchPos = 20
        mapper = mapping.PositionMapper()
        for member in self.members:
            if member.position != None:
                position = mapper.map(member.position, member, self.__grid)
            elif self.__includeBench:
                position = benchPos
                benchPos += 1

            self.__grid[position] = member.skills

    @property
    def members(self):
        return self.__members

    @members.setter
    def members(self, data):
        self.__members = []
        noSkill = []
        for member in data:
            if member["skill"]:
                self.__members.append(Player(member["name"], member["skill"], member["position"]))
            else:
                noSkill.append(member)

        if noSkill:
            avg = np.zeros(34)
            for member in self.__members:
                avg = avg + member.skills
            avg = np.round(avg / len(self.__members))

            for member in noSkill:
                self.__members.append(Player(member["name"], avg.copy(), member["position"]))

        self.__updateGrid()

    @property
    def grid(self):
        return self.__grid


class DataComposer:

    WINNING_LABELS = ["Win A", "Draw", "Win B"]

    def __init__(self, directory: str, includeOldStats=True, includeBench=True, balance=False, scale = True):
        self.__includeBench = includeBench
        self.__includeOldStats = includeOldStats
        self.__balance = balance
        self.__fileLoader = FileLoader(directory)
        self.__scale = scale

    def getMatchWinner(self, score: str):
        arr = score.split("-")
        if arr[0] > arr[1]:
            return self.WINNING_LABELS[0]
        if arr[1] > arr[0]:
            return self.WINNING_LABELS[2]
        return self.WINNING_LABELS[1]

    def parseMatch(self, match):
        result = {"match": [], "result": -1}
        teamA = Team(match["teams"][0], self.__includeBench)
        teamB = Team(match["teams"][1], self.__includeBench)

        result["match"] = np.asarray(list(teamA.grid) + list(teamB.grid))

        if self.__scale:
            result["match"] = np.divide(result["match"], 100)
            
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
            break
        
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
