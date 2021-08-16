# -*- coding: utf-8 -*-
"""
Created on Sun Jul  4 13:25:39 2021

@author: User
"""

import bophono as bp
import pandas as pd
import os
import re
import json
import numpy as np
from utils import *
from parse import *
from dist import *
#from weighted_levenshtein import lev, osa, dam_lev

#Imports
features_phoible = pd.read_csv("data/phonfeatures/phoible-segments-features.tsv", sep='\t') #I have chosen the PHOIBLE features because they are the easiest to use. Another possibility is UPSID features (TBD).
wordlist = pd.read_csv("data/wordlists/general.txt", sep=' ', header = 0)
wordlist.columns = ["bod", "freq"]
features_compo = pd.read_csv("data/phonfeatures/component-feature-table.txt", sep=',')
wordlist_readings_nosyl = pd.read_csv("data/wordlist_readings_nosyl.csv", sep=',')
dists = pd.read_csv("data/mst_dists.csv", sep=',', index_col=0)
dists.rename(columns = {"Unnamed: 78": ''}, index = {np.nan: ''})
with open('data/wordlist_ipa_to_parsed.json', 'r') as f:
    wordlist_ipa_to_parsed = json.load(f)
with open('data/homophone_dict.json', 'r') as f:
    homophone_dict = json.load(f)
mstconverter = bp.UnicodeToApi(schema="MST", options = {'aspirateLowTones': True})




def checkSpell(word, wordlist, wordlist_readings_df, wordlist_readings_parsed, parseFunct, homophone_dict, sylDistFunct, bophono_converter, **kwargs):
    if word in wordlist["bod"]:
        return "No spelling error."
    else:
        wordIPA = mstconverter.get_api(word)
        noSyl = findNoSyl(wordIPA)
        parsedWord = parseFunct(wordIPA)
        sameSylWords = wordlist_readings_df[wordlist_readings_df["nosyl"] == noSyl].filter(items = ["ipa"]).values.flatten().tolist()
        sameSylWords = list(set(sameSylWords).intersection( set(wordlist_readings_parsed.keys())))
        candIPADists = dict()
        for cand in sameSylWords:
            #candIPADists[cand] = getSameLengthWordDist(word, word2, dists, sylDistFunct, **kwargs)
            parsedCand = wordlist_readings_parsed[cand]
            candIPADists[cand] = getSameLengthWordDist(parsedWord, parsedCand, dists, sylDistFunct)
        
        candBod = []
        candBodDists = []
        for cand in sameSylWords:
            currBod = homophone_dict[cand]
            candBod += currBod
            candBodDists += [candIPADists[cand]] * len(currBod)
        
        candidates_ranked = pd.DataFrame({"bod": candBod, "dist": candBodDists}).sort_values("dist")
        
        return candidates_ranked
    
def checkSpellMST(word):
    return checkSpell(word, wordlist, wordlist_readings_nosyl, wordlist_ipa_to_parsed, parseIPAWordMST, homophone_dict, getSylDistanceMST, mstconverter)

checkSpellMST("མཁའ་པ་")
checkSpellMST("གནམ་ཤིད")
checkSpellMST("སྐུ་ཅི་")

#TODO:
#Unexpected segments from bophono
#Add Levenshtein distance between Wylie transcriptions