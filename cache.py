
import json

from os import path
from webscraper import WebScraper

class Cache:
    def __init__(self, autoScrape: bool, fileName=None):
        #check if file is given and exists
        if fileName != None and path.isfile(file):
            #load file and init cache
            file = open(fileName, "r")
            self._matchData = json.load(file)
        else:
            #init empty cache
            self._matchData = {}

        self._autoScrape = autoScrape

    def getMatchData(self, season: int):
        #check if match data is already in cache
        if season in self._matchData:
            #return it
            return self._matchData[season]

        #check if is allowed to automatically scrape missing data
        #allowed seasons are 10 to 19
        elif self._autoScrape and season in range(10, 20):
            ws = WebScraper()
            #get missing season
            self._matchData[season] = ws.getMatches(season)
            return self._matchData[season]

        #not allowed to scrape automatically
        return None

    def save(self):
        file = open("cache.txt", "w+")
        file.write(json.dumps(self._matchData))
        file.close()



cache = Cache(True)
cache.getMatchData(19)
cache.save()
        
