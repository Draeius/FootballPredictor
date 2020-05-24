
import scrapy
import json
import requests
import time
from spiderUtil import FbrefFixtureResponseWrapper, FbrefMatchResponseWrapper

from hashlib import md5
from dateSearch import DateSearch
from itertools import permutations
from scrapy.http import HtmlResponse


class FixturesSpider(scrapy.Spider):
    name = "Fixtures"

    custom_settings = {
        'DOWNLOAD_DELAY': 0.25,
    }

    start_urls = [
        #"https://fbref.com/de/comps/20/2109/schedule/2018-2019-Bundesliga-Fixtures",
        #"https://fbref.com/de/comps/20/1634/schedule/2017-2018-Bundesliga-Fixtures",
        #"https://fbref.com/de/comps/20/1529/schedule/2016-2017-Bundesliga-Fixtures",
        #"https://fbref.com/de/comps/20/1470/schedule/2015-2016-Bundesliga-Fixtures",
        #"https://fbref.com/de/comps/20/736/schedule/2014-2015-Bundesliga-Fixtures",
        #"https://fbref.com/de/comps/9/1889/schedule/2018-2019-Premier-League-Fixtures",
        #"https://fbref.com/de/comps/9/1631/schedule/2017-2018-Premier-League-Fixtures",
        #"https://fbref.com/de/comps/9/1526/schedule/2016-2017-Premier-League-Fixtures",
        #"https://fbref.com/de/comps/9/1467/schedule/2015-2016-Premier-League-Fixtures",
        #"https://fbref.com/de/comps/12/1886/schedule/2018-2019-La-Liga-Fixtures",
        #"https://fbref.com/de/comps/12/1652/schedule/2017-2018-La-Liga-Fixtures",
        #"https://fbref.com/de/comps/12/1547/schedule/2016-2017-La-Liga-Fixtures",
        #"https://fbref.com/de/comps/12/1488/schedule/2015-2016-La-Liga-Fixtures",
        #"https://fbref.com/de/comps/11/1896/schedule/2018-2019-Serie-A-Fixtures",
        #"https://fbref.com/de/comps/11/1640/schedule/2017-2018-Serie-A-Fixtures",
        #"https://fbref.com/de/comps/11/1535/schedule/2016-2017-Serie-A-Fixtures",
        #"https://fbref.com/de/comps/11/1476/schedule/2015-2016-Serie-A-Fixtures",
        "https://fbref.com/en/comps/13/2104/schedule/2018-2019-Ligue-1-Fixtures"
    ]

    leagues = {
        "Premier-League": 13,
        "La-Liga": 53,
        "Bundesliga": 19,
        "Serie-A": 31,
        "Ligue-1": 16
    }

    def __getSeason(self, response) -> str:
        # get the full season string
        seasonStr = response.css("h1[itemprop='name']::text")[0].get()
        # extract the years
        return seasonStr.strip().split(" ")[0]

    def __dumpToFile(self, filePath, toDump):
        dFile = open(filePath, "w+")
        dFile.write(json.dumps(toDump))
        dFile.close()

    def parseTeams(self, response, fileName, matchDate, matchScore, league):
        plSpider = PlayerSpider(matchDate, league)

        wrapper = FbrefMatchResponseWrapper(response, plSpider, matchScore)
        if wrapper.hasField():
            self.__dumpToFile("data/matches/test/" + fileName + ".txt", wrapper.getData())

    def parse(self, response: HtmlResponse):
        season = self.__getSeason(response)
        respWrapper = FbrefFixtureResponseWrapper(response)

        while respWrapper.nextRow():
            # check if there is a score. If there is, there is also a match report
            if respWrapper.hasScore():
                data = respWrapper.extractData()
                toHash = str(time.time()) + str(season) + data["score"] + data["team_a"] + data["team_b"]
                md5Hash = md5(toHash.encode('utf-8'))
                data["match_file"] = str(md5Hash.hexdigest())

                url = respWrapper.generateMatchURL()

                league = ""
                for key in self.leagues:
                    if key in response.url:
                        league = self.leagues[key]

                yield scrapy.Request(url, callback=self.parseTeams, cb_kwargs=dict(
                    fileName=data["match_file"], matchDate=data["date"], matchScore=respWrapper.getMatchScore(), league = league))


class PlayerSpider:

    start_url = "https://www.fifaindex.com/de/players/fifa{season}/"
    url_vars = "?name={name}&league={league}&order=desc"

    def __init__(self, date: str, league: str):
        self.__date = date
        self.__dSearch = DateSearch(date)
        self.__season = self.__dSearch.getSeason(date)
        self.__searchableDates = self.__getSearchableDates()
        self.__searchHref = self.__getSearchHref()
        self.__league = league

    def __getSearchableDates(self):
        response = requests.get(self.start_url.format(season=self.__season))
        basepage = HtmlResponse("", body=response.content, encoding=response.encoding)

        dates = basepage.css("div[class='dropdown-menu fade-out'] > a[class='dropdown-item']")

        result = {}
        for date in dates:
            result[date.css("a::text").get()] = date

        return result

    def permutateName(self, name: str):
        """
        permutates the given name
        """
        return list(permutations(name.split(" |-|'")))

    def __getSearchHref(self) -> str:
        href = None
        keyList = self.__searchableDates.keys()
        while not href:
            try:
                date = self.__dSearch.getNextDate()
                if date in keyList:
                    return "https://www.fifaindex.com" + self.__searchableDates[date].css("a::attr(href)").get()

            except IndexError as err:
                print(err.args[0])
                print(self.__searchableDates.keys())
                break

        raise ValueError("Could not find matching date for " + date)

    def __getPlayerHrefs(self, name: str):
        nameAttempts = self.permutateName(name)

        result = []
        for name in nameAttempts:
            result.append(self.__searchHref + self.url_vars.format(name="+".join(name), league = self.__league))

        return result

    def __getPlayerStats(self, href: str):
        response = requests.get(href)
        playerPage = HtmlResponse("", body=response.content, encoding=response.encoding)
        personalInfo = playerPage.css("div[class='card-body'] > p > span::text").getall()
        ratings = playerPage.css("div[class='card-body'] > p > span > span::text").getall()
        
        return [personalInfo, ratings[-34:]]

    def getPlayer(self, name: str):
        hrefs = self.__getPlayerHrefs(name)

        for href in hrefs:
            response = requests.get(href)
            searchPage = HtmlResponse("", body=response.content, encoding=response.encoding)
            hrefs = searchPage.css("td[data-title='Name'] > a::attr(href)").getall()

            if len(hrefs) == 1:
                return self.__getPlayerStats("https://www.fifaindex.com" + hrefs[0])
        return None

# scrapy runspider spiders.py