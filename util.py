
from itertools import permutations
from typing import List

def permutateName(nameArray):
    """
    permutates the given name
    """
    return list(permutations(nameArray.split(" ")))
