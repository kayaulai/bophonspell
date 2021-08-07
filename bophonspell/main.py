# -*- coding: utf-8 -*-
"""
Created on Sun Jul  4 13:25:39 2021

@author: User
"""

import bophono as bp
import pandas as pd
import csv
import os
import re
from weighted_levenshtein import lev, osa, dam_lev


def checkSpell(word):
    if word in wordlist["bod"]:
        return "Cool"
    else:
        #TODO