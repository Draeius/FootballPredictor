
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
        # ignore additional -pixels -> percentage is sufficient
        return pos  # - int(posString.split("- ")[1][0:-2]))

    def calcPosFromString(self, style: str):
        """
        Maps the given string to an array index indicating the position of the player
        Position is to be given as css style string
        """
        posArray = style.split(";")
        # delete empty entry from last ;
        del posArray[2]
        pos = {}
        for entry in posArray:
            entry = entry.strip()
            posData = entry.split(": calc(")
            posData[-1] = posData[-1][0:-1]
            if posData[0] == "top":
                pos[0] = self.calcPos(posData[1])
            else:
                # invert position if team is displayed on the left side
                # positions are inverted otherwise RV -> LV etc
                # works, because left is always after top in the style
                if posData[0] == "left":
                    pos[0] = 100 - pos[0]
                pos[1] = self.calcPos(posData[1])

        return self.matchPosition(pos)

    def matchPosition(self, pos):
        """
        Searches for a position matching the x and y position given in pos
        """
        # TW
        if pos[0] == 50 and pos[1] == 5:
            return 0
        # RV defensive
        if pos[0] == 17 and pos[1] == 15:
            return 1
        # IV right
        if 33 <= pos[0] and pos[0] <= 34 and pos[1] == 15:
            return 2
        # IV middle
        if pos[0] == 50 and pos[1] == 15:
            return 3
        # IV left
        if 66 <= pos[0] and pos[0] <= 67 and pos[1] == 15:
            return 4
        # LV defensive
        if pos[0] == 83 and pos[1] == 15:
            return 5
        # RF defensive
        if pos[0] == 17 and 20 <= pos[1] and pos[1] <= 30:
            return 6
        # RMF defensive
        if 33 <= pos[0] and pos[0] <= 34 and 20 <= pos[1] and pos[1] <= 30:
            return 7
        # MF defensive
        if 40 <= pos[0] and pos[0] <= 60 and 20 <= pos[1] and pos[1] <= 30:
            return 8
        # LMF defensive
        if 66 <= pos[0] and pos[0] <= 67 and 20 <= pos[1] and pos[1] <= 30:
            return 9
        # LF defensive
        if pos[0] == 83 and 20 <= pos[1] and pos[1] <= 30:
            return 10
        # RF offensive
        if pos[0] == 17 and 30 < pos[1] and pos[1] <= 40:
            return 11
        # RMF offensive
        if 33 <= pos[0] and pos[0] <= 34 and 30 < pos[1] and pos[1] <= 40:
            return 12
        # MF offensive
        if pos[0] == 50 and 30 < pos[1] and pos[1] <= 40:
            return 13
        # LMF offensive
        if 66 <= pos[0] and pos[0] <= 67 and 30 < pos[1] and pos[1] <= 40:
            return 14
        # LF offensive
        if pos[0] == 83 and 30 < pos[1] and pos[1] <= 40:
            return 15
        # RS
        if pos[0] == 25 and 40 < pos[1] and pos[1] <= 50:
            return 16
        # MS
        if pos[0] == 50 and 40 < pos[1] and pos[1] <= 50:
            return 17
        # LS
        if pos[0] == 75 and 40 < pos[1] and pos[1] <= 50:
            return 18

        # position could not be found. Raise an error
        raise NoMatchError(
            "The position top: " + str(pos[0]) + ", left: " + str(pos[1]) + " has no match.")
