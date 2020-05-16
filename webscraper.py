
import pprint

import requests
from bs4 import BeautifulSoup
from progress.bar import ChargingBar


class NoMatchError(ValueError):
    """
    Exception that indicates, that no match has been found
    """
    pass

class PositionMapper:
    """
    Maps the position data in a css style string to the position on the field.
    """

    def calcPos(self, posString: str) -> int:
        """
        calculate the position given by the string
        """
        pos = round(float(posString.split("%")[0]))
        #ignore additional -pixels -> percentage is sufficient
        return pos# - int(posString.split("- ")[1][0:-2]))

    def calcPosFromString(self, style: str):
        """
        Maps the given string to an array index indicating the position of the player
        Position is to be given as css style string
        """
        posArray = style.split(";")
        #delete empty entry from last ;
        del posArray[2]
        pos = {}
        for entry in posArray:
            entry = entry.strip()
            posData = entry.split(": calc(")
            posData[-1] = posData[-1][0:-1]
            if posData[0] == "top":
                pos[0] = self.calcPos(posData[1])
            else:
                #invert position if team is displayed on the left side
                #positions are inverted otherwise RV -> LV etc
                #works, because left is always after top in the style
                if posData[0] == "left":
                    pos[0] = 100 - pos[0]
                pos[1] = self.calcPos(posData[1])

        return self.matchPosition(pos)
    
    def matchPosition(self, pos):
        """
        Searches for a position matching the x and y position given in pos
        """
        #TW
        if pos[0] == 50 and pos[1] == 5:
            return 0
        #RV defensive
        if pos[0] == 17 and pos[1] == 15:
            return 1
        #IV right
        if 33 <= pos[0] and pos[0] <= 34 and pos[1] == 15:
            return 2
        #IV middle
        if pos[0] == 50 and pos[1] == 15:
            return 3 
        #IV left
        if 66 <= pos[0] and pos[0] <= 67 and pos[1] == 15:
            return 4
        #LV defensive
        if pos[0] == 83 and pos[1] == 15:
            return 5
        #RF defensive
        if pos[0] == 17 and 20 <= pos[1] and pos[1] <= 30:
            return 6
        #RMF defensive
        if 33 <= pos[0] and pos[0] <= 34 and 20 <= pos[1] and pos[1] <= 30:
            return 7
        #MF defensive
        if 40 <= pos[0] and pos[0] <= 60 and 20 <= pos[1] and pos[1] <= 30:
            return 8
        #LMF defensive
        if 66 <= pos[0] and pos[0] <= 67 and 20 <= pos[1] and pos[1] <= 30:
            return 9
        #LF defensive
        if pos[0] == 83 and 20 <= pos[1] and pos[1] <= 30:
            return 10
        #RF offensive
        if pos[0] == 17 and 30 < pos[1] and pos[1] <= 40:
            return 11
        #RMF offensive
        if 33 <= pos[0] and pos[0] <= 34 and 30 < pos[1] and pos[1] <= 40:
            return 12
        #MF offensive
        if pos[0] == 50 and 30 < pos[1] and pos[1] <= 40:
            return 13
        #LMF offensive
        if 66 <= pos[0] and pos[0] <= 67 and 30 < pos[1] and pos[1] <= 40:
            return 14
        #LF offensive
        if pos[0] == 83 and 30 < pos[1] and pos[1] <= 40:
            return 15
        #RS
        if pos[0] == 25 and 40 < pos[1] and pos[1] <= 50:
            return 16
        #MS
        if pos[0] == 50 and 40 < pos[1] and pos[1] <= 50:
            return 17
        #LS
        if pos[0] == 75 and 40 < pos[1] and pos[1] <= 50:
            return 18
        
        #position could not be found. Raise an error
        raise NoMatchError("The position top: " + str(pos[0]) + ", left: " + str(pos[1]) + " has no match.")


class WebScraper:

    ERSTE_BUNDESLIGA = "Fußball-Bundesliga"
    ZWEITE_BUNDESLIGA = "2. Fußball Bundesliga"

    #seasons are one ahead for fifa. season 19/20 is fifa 20
    FIFA_URL = "https://www.fifaindex.com/de/players/fifa{season}/?name={fName}+{lName}&order=desc"

    FBREF_URL = "https://fbref.com/en/comps/20/2109/schedule/{season}-Bundesliga-Fixtures"
    FBREF_BASE_URL = "https://fbref.com"

    
    def _loadPage(self, href: str) -> BeautifulSoup:
        #Load the requested page
        page = requests.get(href)
        #create and return beautifulSoup
        return BeautifulSoup(page.content, features="html.parser")

    def _getBasePage(self, season: int) -> BeautifulSoup:
        """
        Creates a BeautifulSoup object that contains the page
        """
        #create the season string for the season beginning in year 'season'
        seasonString = "20{}-20{}".format(season, season+1)
        #format the url and load page
        return self._loadPage(self.FBREF_URL.format(season = seasonString))
       
    def _getCaptians(self, soup: BeautifulSoup):
        """
        Extracts the captains from the given page
        """
        #find scorebox, where captains are listed
        scorebox = soup.find("div", attrs={"class": "scorebox"})
        #find all leaders, including coaches
        leaders = scorebox.findChildren("div", attrs={"class": "datapoint"})

        captains = []
        #iterate all leaders
        for leader in leaders:
            #captains are players and therefore have a link
            href = leader.findChildren("a")
            if href:
                #whitespaces are masced...
                captains.append(href[0].contents[0].replace("\xa0", " "))

        return captains

    def _getFormationOfTeam(self, playerList, team, field, posMapper: PositionMapper):
        """
        Extracts the formation of a given team from the given field
        """
        #19 possible positions + bench
        formation = [None]*20
        #create bench
        formation[19] = []

        for player in playerList:
            #check if player is indeed a player and not some other data
            if type(player) == type(1):
                try:
                    #find div of the player on the field
                    playerDiv = field.find("div", string=player, attrs={"class": "poptip " + team})
                    #if div was found
                    if playerDiv != None:
                        #extract css position
                        style = playerDiv["style"]
                        #map the player to his position
                        position = posMapper.calcPosFromString(style)
                        if formation[position] == None:
                            formation[position] = player
                        #try to solve an issues with some formations where they have two MF behind each other
                        elif position == 8 and formation[13] == None:
                            #position the second MF as MFO
                            formation[13] = player
                        #still not solved -.-
                        else:
                            raise NoMatchError("Matching two players for one position. Players: " + str(player) + ", " + str(formation[position]))
                    #div not found -> player is on bench
                    else:
                        formation[19].append(player)
                except NoMatchError as err:
                    raise err

        return formation

    def _getFormation(self, soup: BeautifulSoup, pData):
        """
        Extracts the formation of the two parties in the given match
        """
        #create empty formation
        formation = {"a": None, "b": None}
        #find the field in the page
        field = soup.find("div", attrs={"id": "field"})

        #create a Mapper to map all positions
        posMapper = PositionMapper()

        #iterate teams
        for team in pData:
            #build formation of the current team (team "a" and "b")
            formation[team] = self._getFormationOfTeam(pData[team], team, field, posMapper)

        return formation

    def _findTeamMembers(self, team: BeautifulSoup):
        """
        Extracts the members of a team from the given soup
        """
        #extract all table rows
        rowArray = team.findChildren("tr")
        #create empty result
        pMap = {}

        #iterate all potential players
        for row in rowArray:
            #search for rows data
            data = row.findChildren("td")
            #potentially no data, because of table headers for bench
            if data != []:
                #find player name and number
                pName = data[1].find("a").contents[0]
                pNumber = int(data[0].contents[0])
                
                #append result
                pMap[pNumber] = pName
        return pMap

    def _getMatchData(self, matchURL: str):
        """
        Loads the match with the given url and extracts the given data
        """
        #create empty match data
        mData = {"a": {}, "b": {}}

        #load the page
        soup = self._loadPage(matchURL)
        
        #extract captains
        captains = self._getCaptians(soup)
        mData["a"]["captain"] = captains[0]
        mData["b"]["captain"] = captains[1]

        #find both teams on the page
        teams = soup.find("div", attrs={"id": "field_wrap"}).findChildren("table")
        #iterate teams
        for team in teams:
            #extract if team is team "a" or "b"
            tId = team.find_parent("div", attrs={"class": "lineup"})["id"]
            #find team members
            mData[tId] = self._findTeamMembers(team)

        try:
            #try to create a formation
            formation = self._getFormation(soup, mData)

            #add team formations to match data
            mData["a"]["formation"] = formation["a"]
            mData["b"]["formation"] = formation["b"]
        except NoMatchError as err:
            #may fail in case there is a position, that is not known by the mapper
            print("In match: " + matchURL)
            print(err.args[0])
            return None
            
        return mData

    def _determineWinner(self, score: str):
        """
        Determines the winner of a match.
        Returns a for home, b for away, None for draw
        """
        #split the score
        arr = score.split("–")
        #check home winner
        if arr[0] > arr[1]:
            return "a"
        #check away winner
        if arr[1] > arr[0]:
            return "b"
        #no winner
        return None

    def getMatches(self, season: int):
        """
        Loads all matches of the given season and extracts their data, such as players, formation and captains
        """
        #load list of all matches for the given season
        soup = self._getBasePage(season)

        #find tbody element of the table that contains all matches of the season
        table = soup.find_all("table", id = lambda x: x and x.startswith('sched_ks_'))[1].findChildren("tbody")[0]
        #find all table rows that contain a match
        rows = table.findChildren("tr", attrs={"class": None})

        #empty result
        result = []
        #create a handy charging bar to see the progress
        cb = ChargingBar("loading season 20" + str(season), max=len(rows))

        #iterarte all table rows
        for game in rows:
            #find data entries in the rows
            dEntries = game.findChildren("td")
            #append the time of the game
            result.append({
                "time": dEntries[2].find("span").contents[0]
            })
            result[-1]["winner"] = self._determineWinner(dEntries[5].find("a").contents[0])
            #extract URL to match
            matchURL = self.FBREF_BASE_URL + dEntries[11].find("a")["href"]
            #append match data
            result[-1]["data"] = self._getMatchData(matchURL)
            #next step in the progress bar
            cb.next()
        cb.finish()
        return result

ws = WebScraper()
matches = ws.getMatches(19)

#pp = pprint.PrettyPrinter(indent=4)
#pp.pprint(matches[-1])
