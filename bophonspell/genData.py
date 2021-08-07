# -*- coding: utf-8 -*-
"""
Created on Sun Jul  4 13:25:39 2021

@author: Ryan Ka Yau Lai

The code for generating some of the data in the data/ folder. Not intended for public use.
"""

import bophono as bp
import pandas as pd
import csv
import os
import re
from weighted_levenshtein import lev, osa, dam_lev


#From shadowtalker: https://stackoverflow.com/questions/21292552/equivalent-of-paste-r-to-python
from functools import reduce

def _reduce_concat(x, sep=""):
    return reduce(lambda x, y: str(x) + sep + str(y), x)
        
def paste(*lists, sep=" ", collapse=None):
    result = map(lambda x: _reduce_concat(x, sep=sep), zip(*lists))
    if collapse is not None:
        return _reduce_concat(result, sep=collapse)
    return list(result)


syl = "འགྲའ་"
os.chdir("G:/我的雲端硬碟/1. Current research/bophonspell") #Change to current folder

#Import feature data
features_phoible = pd.read_csv("data/phonfeatures/phoible-segments-features.tsv", sep='\t') #I have chosen the PHOIBLE features because they are the easiest to use. Another possibility is UPSID features (TBD).

#Create the bophono converter
options = {
  'aspirateLowTones': True
}
mstconverter = bp.UnicodeToApi(schema="MST", options = options)
mstipa = mstconverter.get_api(syl)
print(mstipa)

#Import the wordlist
wordlist = pd.read_csv("data/wordlists/general.txt", sep=' ', header = 0)
wordlist.columns = ["bod", "freq"]
wordlist_ipa = [""] * len(wordlist)
homophone_dict = {}

for i, row in wordlist.iterrows():
    curr_ipa = mstconverter.get_api(row["bod"])
    wordlist_ipa[i] = curr_ipa
    if curr_ipa in homophone_dict.keys():
        homophone_dict[curr_ipa] = homophone_dict[curr_ipa] + [row["bod"]]
    else:
        homophone_dict[curr_ipa] = [row["bod"]]

vowels_mst = ['e', 'ɛ', 'ɔ', 'o', 'ø', 'i', 'a', 'ə', 'u', 'e', 'y']
vowels_mst = vowels_mst + paste(vowels_mst, 'ː' * len(vowels_mst), sep = "")
vowel_diac_mst = ['̃']
tones_mst = ['ˊ', 'ˋ']


def parseIPASylMST(syl):
    return parseIPASyl(syl, vowels_mst, vowel_diac_mst, tones_mst)
    
def parseIPASyl(syl, vowels, vowel_diac, tones):
    vow_span = re.search(getListRE(vowels) + "+" + getListRE(vowel_diac) + "*", syl).span()
    tone_re = re.search(getListRE(tones), syl)
    if tone_re is not None:
        tone_span = tone_re.span()
        if vow_span[1] != tone_span[0]:
            raise Exception("Potential error in vowel/tone list: vow_end = " + str(vow_span[1]) + "; tone start: " + str(tone_span[0]))
            
        long = False
        if len(syl) > tone_span[1]:
            if syl[tone_span[1]] == "ː":
                long = True
        if not long:
            result = [syl[:vow_span[0]], syl[vow_span[0]:vow_span[1]], syl[tone_span[0]:tone_span[1]], syl[(tone_span[1]):]]
        else:
            result = [syl[:vow_span[0]], syl[vow_span[0]:vow_span[1]] + "ː", syl[tone_span[0]:tone_span[1]], syl[(tone_span[1] + 1):]]
    else:
        long = False
        if len(syl) > vow_span[1]:
            if syl[vow_span[1]] == "ː":
                long = True
        if not long:
            result = [syl[:vow_span[0]], syl[vow_span[0]:vow_span[1]], "", syl[(vow_span[1]):]]
        else: 
            result = [syl[:vow_span[0]], syl[vow_span[0]:vow_span[1]] + "ː", "", syl[(vow_span[1] + 1):]]
    return result

def parseIPAWordMST(word):
    return [parseIPASylMST(syl) for syl in word.split(".")]
        
def detectNucWordMST(word):
    return all([re.search(getListRE(vowels_mst) + "+" + getListRE(vowel_diac_mst) + "*", syl) is not None for syl in word.split(".")])
    
    
def getListRE(options):
    return "[" + "|".join(options) + "]"

onsets_mst = []
codas_mst = []
nonuc_mst = []
vowels_mst_combined = []
for word in homophone_dict.keys():
    if not detectNucWordMST(word):
        #If not all syllables have a nucleus
        nonuc_mst = nonuc_mst + [word]
    elif word not in [""]:
        parsed = parseIPAWordMST(word)
        for syl in parsed:
            if syl[0] not in onsets_mst:
                onsets_mst = onsets_mst + [syl[0]]
            if syl[1] not in vowels_mst_combined:
                vowels_mst_combined = vowels_mst_combined + [syl[1]]
            if syl[3] not in codas_mst:
                codas_mst = codas_mst + [syl[3]]

def ipaToFeat(ipa, featTable, fieldname = "segment"):
    seg = ipa
    vec = featTable[featTable[fieldname] == seg].drop(fieldname, axis=1).values.flatten().tolist()
    return vec

segs_mst = list(set(onsets_mst + codas_mst + vowels_mst_combined))
seg_feats_list = list(map(lambda x: ipaToFeat(x, features_phoible, "segment"), segs_mst))
seg_feats = dict()
for i, seg in enumerate(segs_mst):
    seg_feats[seg] = seg_feats_list[i]
    if seg_feats_list[i] == []:
        print(seg)
        
