
import scrapy
import json

from hashlib import md5


class FixturesSpider(scrapy.Spider):
    name = "Fixtures"

    custom_settings = {
        'DOWNLOAD_DELAY': 0.25,
    }

    start_urls = [
        "https://fbref.com/de/comps/20/2109/schedule/2018-2019-Bundesliga-Fixtures",
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
        
    def __parseSingleTeam(self, team, field):
        result = []
        playerList = team.css("tr")
        for player in playerList:
            data = player.css("td")
            if data:
                name = data[1].css("a::text").get()
                result.append(
                    {"number": int(data[0].css("::text").get()),
                     "name": name,
                     "position": self.__parsePosition(name, field)
                     })
        return result

    def __dumpToFile(self, filePath, toDump):
        dFile = open(filePath, "w+")
        dFile.write(json.dumps(toDump))
        dFile.close()

    def parse_teams(self, response, fileName):
        result = []
        teams = response.css("div[class='lineup'] > table")
        field = response.css("div[id='field']")
        if not field:
            return
        
        field = field[0]
        for team in teams:
            result.append(self.__parseSingleTeam(team, field))

        self.__dumpToFile("data/matches/mData/" + fileName + ".txt", result)

    def parse(self, response):
        season = self.__getSeason(response)
        matches = self.__getMatchTable(response).css(
            "tr:not([class^='spacer partial_table'])").css("tr:not([class^='thead'])")

        matchList = []
        for match in matches:
            mData = {}
            #check if there is a score. If there is, there is also a match report
            score = match.css("td[data-stat='score'] > a::text").get()
            if score != None:
                mData["date"] = match.css("td[data-stat='date'] > a::text").get()
                mData["score"] = score.strip().replace("–", "-")
                mData["team_a"] = match.css("td[data-stat='squad_a'] > a::text").get()
                mData["team_b"] = match.css("td[data-stat='squad_b'] > a::text").get()
                mData["match_file"] = season + "/" + str(md5((mData["score"] + mData["team_a"] + mData["team_b"]).encode('utf-8')).hexdigest())
                matchList.append(mData)
                url = "https://fbref.com" + match.css("td[data-stat='match_report'] > a::attr(href)").get()
                
                yield scrapy.Request(url, callback=self.parse_teams, cb_kwargs=dict(fileName=mData["match_file"]))

        self.__dumpToFile("data/matches/" + season + ".txt", matchList)

# scrapy runspider spiders.py
