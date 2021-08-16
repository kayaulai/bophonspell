# -*- coding: utf-8 -*-
"""
Created on Mon Aug 16 01:47:50 2021

@author: User
"""
#From shadowtalker: https://stackoverflow.com/questions/21292552/equivalent-of-paste-r-to-python
from functools import reduce

def _reduce_concat(x, sep=""):
    return reduce(lambda x, y: str(x) + sep + str(y), x)
        
def paste(*lists, sep=" ", collapse=None):
    result = map(lambda x: _reduce_concat(x, sep=sep), zip(*lists))
    if collapse is not None:
        return _reduce_concat(result, sep=collapse)
    return list(result)

def getListRE(options):
    return "[" + "|".join(options) + "]"

