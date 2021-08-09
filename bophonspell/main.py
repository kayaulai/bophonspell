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
import json
#from weighted_levenshtein import lev, osa, dam_lev

#Imports
features_phoible = pd.read_csv("data/phonfeatures/phoible-segments-features.tsv", sep='\t') #I have chosen the PHOIBLE features because they are the easiest to use. Another possibility is UPSID features (TBD).
wordlist = pd.read_csv("data/wordlists/general.txt", sep=' ', header = 0)
wordlist.columns = ["bod", "freq"]
features_compo = pd.read_csv("data/phonfeatures/component-feature-table.txt", sep=',')
wordlist_readings_nosyl = pd.read_csv("data/wordlist_readings_nosyl.csv", sep=',')
dists = pd.read_csv("data/mst_dists.csv", sep=',')
with open('data/wordlist_ipa_to_parsed.json', 'r') as f:
    wordlist_ipa_to_parsed = json.load(f)
with open('data/homophone_dict.json', 'r') as f:
    homophone_dict = json.load(f)
mstconverter = bp.UnicodeToApi(schema="MST", options = {'aspirateLowTones': True})


#Accepts PARSED syllables as input (i.e. vector with four components)
#For non-tonal varieties, leave third component blank
#zeroInitialAsGlottal = treat initial zeroes as glottal stops, rather than indel
#finalRTDivisor = How much to divide when there is final r/l vs no coda

def findNoSyl(ipa):
    return len(re.findall("\.", ipa)) + 1
wordlist_readings = pd.DataFrame({"ipa": homophone_dict.keys(), "nosyl": [findNoSyl(x) for x in homophone_dict.keys()]})

def parseIPAWordMST(word):
    print(word)
    return [parseIPASylMST(syl) for syl in word.split(".")]



def getSylDistanceMST(syl1, syl2, dists, weights = [.4, .2, .2, .2], zeroInitialAsGlottal = True, finalRTDivisor = 2):
    if zeroInitialAsGlottal:
        if syl1[0] == "":
            syl1[0] = "ʔ"
        if syl2[0] == "":
            syl2[0] = "ʔ"
    
    onsetDist = dists[syl1[0]][syl2[0]]
    nucDist = dists[syl1[1]][syl2[1]]
    #Tone dist is twice the indel cost
    toneDist = int(syl1[2] != syl2[2]) * dists[""]["d"] * 2
    codaDist = dists[syl1[3]][syl2[3]]
    
    #r, l, zero should be more similar to each other
    if syl1[3] in ["r", "l", ""] and syl2[3] in ["r", "l", ""]:
        codaDist = codaDist / finalRTDivisor
    
    return onsetDist * weights[0] + nucDist * weights[1] + toneDist * weights[2] + codaDist * weights[3]    

#Takes PARSED words.
def getSameLengthWordDist(word1, word2, dists, sylDistFunct, **kwargs):
    if len(word1) != len(word2):
        raise Exception("The words must be of the same length.")
    totalDist = 0
    for i in range(0, len(word1)):
        syl1 = word1[i]
        syl2 = word2[i]
        totalDist += sylDistFunct(syl1, syl2, dists, **kwargs)
    return totalDist

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

#TODO:
#Unexpected segments from bophono
#Add Levenshtein distance between Wylie transcriptions