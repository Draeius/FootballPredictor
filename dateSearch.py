import calendar
import datetime
import locale


class DateSearch:

    def __init__(self, startDate, searchDepth=185):
        self._startDate = self.__parseDate(startDate)
        self._offset = 0
        self._searchDepth = searchDepth

    def __parseDate(self, date):
        if "-" in date:
            return datetime.datetime.strptime(date, '%Y-%m-%d')
        else:
            return datetime.datetime.strptime(date, '%d.%m.%Y')

    def nextOffset(self):
        self._offset *= -1
        if self._offset >= 0:
            self._offset += 1

        if self._offset > self._searchDepth:
            raise IndexError("date offset out of bounds for start date: " + self._startDate.strftime("%d.%m.%Y") +
                             "; season: " + str(self.__getSeasonFromDate(self._startDate)))

    def __getSeasonFromDate(self, date):
        if int(date.strftime("%m")) >= 9:
            return str(int(date.strftime("%y"))+1)
        else:
            return date.strftime("%y")

    def getSeason(self, date):
        return self.__getSeasonFromDate(self.__parseDate(date))

    def getNextDate(self):
        locale.setlocale(locale.LC_ALL, 'de_DE')
        date = self._startDate + datetime.timedelta(self._offset)
        self.nextOffset()
        return date.strftime("%d. %B %Y")
