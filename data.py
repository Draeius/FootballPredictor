
import json
import mapping

from sklearn import preprocessing

class DataComposer:

    def __init__(self, includeBench=True):
        self.__includeBench = includeBench

    def __fixPosition(self, position):
        switcher = {
            2: 7,
            3: 8,
            4: 9,
            7: 12,
            8: 13,
            9: 14,
            12: 16,
            13: 17,
            14: 18
        }
        return switcher[position]

    def getMatchWinner(self, score: str):
        arr = score.split("-")
        if arr[0] > arr[1]:
            return -1
        if arr[1] > arr[0]:
            return 1
        return 0

    def getPlayerSkill(self, team, player):
        if "skill" in player.keys() and player["skill"] != None:
            return int(player["skill"])

        totalSkill = 0
        for member in team:
            if "skill" in member.keys() and member["skill"] != None:
                totalSkill += int(member["skill"])

        return round(totalSkill / len(team))

    def getTeam(self, team):
        if self.__includeBench:
            result = [0]*28
        else:
            result = [0]*19
        mapper = mapping.PositionMapper()
        benchPos = 19
        for member in team:
            if member["position"] != None:
                try:
                    position = mapper.matchPosition([member["position"]["top"], member["position"]["left"]])
                except:
                    print("During player " + member["name"])
                    raise

                if result[position] != 0 and result[position] != self.getPlayerSkill(team, member):
                    # fix some issues with some formations
                    newPosition = self.__fixPosition(position)
                    if result[newPosition] != 0:
                        print(result[0:19])
                        print(result[19:len(result)])
                        raise IndexError("Position " + str(newPosition) + " already in use. Original position: " + str(position) + " Can not assign " + member["name"])
                    position = newPosition
            elif self.__includeBench:
                position = benchPos
                benchPos += 1

            result[position] = self.getPlayerSkill(team, member)
        return result

    def getGameVector(self, filePath: str):
        try:
            path = "data/matches/mData/" + filePath + ".txt"
            file = open(path)
        except:
            return None

        game = json.load(file)
        gameVector = []
        for team in game:
            gameVector += self.getTeam(team)

        return gameVector

    def getSeason(self, season: int):
        path = "data/matches/20{}-20{}.txt".format(season-1, season)
        file = open(path)

        seasonData = json.load(file)
        result = {"matches": [], "results": []}
        for game in seasonData:
            try:
                vector = self.getGameVector(game["match_file"])
            except KeyError as err:
                if err.args[0] != "skill":
                    continue
                else:
                    raise
            except:
                print("Error occured in match '" + game["team_a"] + "' against '" + game["team_b"] + "', " + game["date"])
                raise

            if vector:
                result["matches"].append(vector)
                result["results"].append(self.getMatchWinner(game["score"]))
            else:
                print("failed to find match '" + game["team_a"] + "' against '" + game["team_b"] + "', " + game["date"])

        return result

    def getData(self, seasonArray):
        result = {"matches": [], "results": []}
        for season in seasonArray:
            temp = self.getSeason(season)
            result["matches"] += temp["matches"]
            result["results"] += temp["results"]
        
        result["matches"] = preprocessing.scale(result["matches"])
        return result

