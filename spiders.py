
import scrapy
import json
import requests

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
        # "https://fbref.com/de/comps/20/2109/schedule/2018-2019-Bundesliga-Fixtures",
         "https://fbref.com/de/comps/20/1634/schedule/2017-2018-Bundesliga-Fixtures",
         "https://fbref.com/de/comps/20/1529/schedule/2016-2017-Bundesliga-Fixtures",
         "https://fbref.com/de/comps/20/1470/schedule/2015-2016-Bundesliga-Fixtures",
         "https://fbref.com/de/comps/20/736/schedule/2014-2015-Bundesliga-Fixtures"
    ]

    def __getSeason(self, response) -> str:
        # get the full season string
        seasonStr = response.css("h1[itemprop='name']::text")[0].get()
        # extract the years
        return seasonStr.strip().split(" ")[0]

    def __getMatchTable(self, response):
        # extract tbody of the table containing the matches
        return response.css("table[id='sched_ks_all']")[0].css("tbody")[0]

    def __parsePosition(self, name, field):
        styleSelector = field.css('div[title="' + name + '"]').xpath("@style").extract()
        if not styleSelector:
            return None

        styleArray = styleSelector[0].split(";")
        del styleArray[2]

        result = {}
        switch = False
        for style in styleArray:
            temp = style.split(": calc(")
            key = temp[0].strip()
            value = round(float(temp[1].split("%")[0]))
            if key == "right":
                switch = True
                key = "left"
            result[key] = value

        if switch:
            result["top"] = 100 - result["top"]

        return result

    def __parseSingleTeam(self, team, field, date):
        result = []
        playerList = team.css("tr")
        plSpider = PlayerSpider(date)
        for player in playerList:
            data = player.css("td")
            if data:
                name = data[1].css("a::text").get()
                result.append(
                    {"number": int(data[0].css("::text").get()),
                     "name": name,
                     "position": self.__parsePosition(name, field),
                     "skill": plSpider.getPlayer(name)
                     })
        return result

    def __dumpToFile(self, filePath, toDump):
        dFile = open(filePath, "w+")
        dFile.write(json.dumps(toDump))
        dFile.close()

    def parse_teams(self, response, fileName, matchDate):
        result = []
        teams = response.css("div[class='lineup'] > table")
        field = response.css("div[id='field']")
        if not field:
            return

        field = field[0]
        for team in teams:
            result.append(self.__parseSingleTeam(team, field, matchDate))

        self.__dumpToFile("data/matches/mData/" + fileName + ".txt", result)

    def parse(self, response):
        season = self.__getSeason(response)
        matches = self.__getMatchTable(response).css(
            "tr:not([class^='spacer partial_table'])").css("tr:not([class^='thead'])")

        matchList = []
        for match in matches:
            mData = {}
            # check if there is a score. If there is, there is also a match report
            score = match.css("td[data-stat='score'] > a::text").get()
            if score != None:
                mData["date"] = match.css("td[data-stat='date'] > a::text").get()
                mData["score"] = score.strip().replace("–", "-")
                mData["team_a"] = match.css("td[data-stat='squad_a'] > a::text").get()
                mData["team_b"] = match.css("td[data-stat='squad_b'] > a::text").get()
                mData["match_file"] = season + "/" + str(md5((mData["score"] + mData["team_a"] + mData["team_b"]).encode('utf-8')).hexdigest())
                matchList.append(mData)
                url = "https://fbref.com" + match.css("td[data-stat='match_report'] > a::attr(href)").get()

                yield scrapy.Request(url, callback=self.parse_teams, cb_kwargs=dict(fileName=mData["match_file"], matchDate=mData["date"]))

        self.__dumpToFile("data/matches/" + season + ".txt", matchList)


class PlayerSpider:

    start_url = "https://www.fifaindex.com/de/players/fifa{season}/"
    url_vars = "?name={name}&league=19&order=desc"

    def __init__(self, date: str):
        self.__date = date
        self.__dSearch = DateSearch(date)
        self.__season = self.__dSearch.getSeason(date)
        self.__searchableDates = self.__getSearchableDates()
        self.__searchHref = self.__getSearchHref()

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
        return list(permutations(name.split(" ")))

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
            result.append(self.__searchHref + self.url_vars.format(name="+".join(name)))

        return result

    def getPlayer(self, name: str):
        hrefs = self.__getPlayerHrefs(name)

        for href in hrefs:
            response = requests.get(href)
            searchPage = HtmlResponse("", body=response.content, encoding=response.encoding)
            hrefs = searchPage.css("td[data-title='GES / POT'] > span::text").getall()

            if len(hrefs) == 2:
                return int(hrefs[0])
        return None

# scrapy runspider spiders.py
