

from typing import Dict, List
from scrapy.http import HtmlResponse
from scrapy.selector import Selector


class AbstractFbrefResponseWrapper:

    def __init__(self, response: HtmlResponse):
        self._response = response

    def getResponse(self) -> HtmlResponse:
        return self._response


class FbrefFixtureResponseWrapper(AbstractFbrefResponseWrapper):
    """
    Wraps the response of a request to get fixtures from fbref.com to provide utility methods
    """
    TEAMS = ["a", "b"]

    def __init__(self, response: HtmlResponse):
        super().__init__(response)
        self.__tableRows = self._response.css("table[id='sched_ks_all']")[0].css(
            "tbody > tr:not([class^='thead'])").css("tr:not([class^='spacer partial_table'])")
        self.__currentRow = -1
        self.__rowCount = len(self.__tableRows)

    def __getDataField(self, field: str) -> str:
        return self.__tableRows[self.__currentRow].css("td[data-stat='" + field + "'] > a::text").get()

    def nextRow(self) -> bool:
        """
        Advances to the next row if there are still more. Returns true if there are, false otherwise
        """
        if self.hasNextRow():
            self.__currentRow += 1
            return True

        return False

    def hasNextRow(self) -> bool:
        """
        Checks if there are still more data rows
        """
        return self.__currentRow + 1 < self.__rowCount

    def getMatchDate(self) -> str:
        """
        Searches for the date of a match in the current row
        """
        return self.__getDataField("date")

    def getMatchScore(self) -> str:
        """
        Searches for the score of a match in the current row
        """
        score = self.__getDataField("score")
        # some matches do not have a score
        if not score:
            return None

        # change scome characters in the score to make it easier afterwards
        return score.strip().replace("–", "-")

    def getSquadName(self, squad: str) -> str:
        """
        Determines the name of either squad a or b
        """
        return self.__getDataField("squad_" + squad)

    def generateMatchURL(self) -> str:
        """
        Generates a full URL to the match report of the current match
        """
        return "https://fbref.com" + self.__tableRows[self.__currentRow].css("td[data-stat='match_report'] > a::attr(href)").get()

    def hasScore(self) -> bool:
        """
        Checks if the match at the current row has a score. in other words, checks if the match is yet to take place
        """
        return bool(self.getMatchScore())

    def extractData(self) -> Dict[str, str]:
        """
        Extracts the match data for the current row from the response
        """
        if self.hasScore():
            result = {}
            result["date"] = self.getMatchDate()
            result["score"] = self.getMatchScore()
            for team in self.TEAMS:
                result["team_" + team] = self.getSquadName(team)

            return result
        return None


class FbrefMatchResponseWrapper(AbstractFbrefResponseWrapper):
    """
    Wraps the response of a request to get a single match from fbref.com to provide utility methods
    """

    def __init__(self, response: HtmlResponse, playerSpider):
        super().__init__(response)
        self.__field = response.css("div[id='field']")
        self.__teams = []
        if self.hasField():
            self.__field = self.__field[0]
            self.__teamSelector = response.css("div[class='lineup'] > table")
            for team in self.__teamSelector:
                self.__teams.append(Team(team, self.__field, playerSpider))

    def hasField(self) -> bool:
        """
        Determines if this match has an element that displays the lineup of the game
        """
        return bool(self.__field)

    def getTeams(self):
        return [team.toArray() for team in self.__teams]


class Team:

    def __init__(self, teamSelector: Selector, positions: Selector, playerSpider):
        self.__teamSelector = teamSelector.css("tr")
        # delete headers from team table
        del self.__teamSelector[12]
        del self.__teamSelector[0]

        self.__members = []
        for selector in self.__teamSelector:
            self.__members.append(Member(selector.css("td"), positions, playerSpider))

    def __iter__(self):
        self.__index = 0
        return self

    def __next__(self):
        if self.__index < len(self.__members):
            result = self.__members[self.__index]
            self.__index += 1
            return result

        raise StopIteration

    def toArray(self):
        return [member.encode() for member in self]


class Member:

    def __init__(self, data: Selector, positions: Selector, playerSpider):
        self.__playerSpider = playerSpider
        self.__name = data[1].css("::text").get()
        self.__number = int(data[0].css("::text").get())
        self.__position = positions.css('div[title="' + self.__name + '"]').xpath("@style").extract()
        if not self.__position:
            self.__position = None
        else:
            self.__position = self.__calcPosition()

    def __calcPosition(self):
        styleArray = self.__position[0].split(";")
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

    def encode(self):
        return {"number": self.__number,
                "name": self.__name,
                "position": self.__position,
                "skill": self.__playerSpider.getPlayer(self.__name)
                }
