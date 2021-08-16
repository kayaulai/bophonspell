# -*- coding: utf-8 -*-
"""
Created on Sun Jul  4 13:25:39 2021

@author: Ryan Ka Yau Lai

The code for generating some of the data in the data/ folder. Not intended for public use.
"""

import bophono as bp
import pandas as pd
import os
import re
import json
from utils import *
from parse import *
from dist import *


os.chdir("G:/我的雲端硬碟/1. Current research/bophonspell") #Change to current folder

#Import feature data
features_phoible = pd.read_csv("data/phonfeatures/phoible-segments-features.tsv", sep='\t') #I have chosen the PHOIBLE features because they are the easiest to use. Another possibility is UPSID features (TBD).
features_compo = pd.read_csv("data/phonfeatures/component-feature-table.txt", sep=',')


#Create the bophono converter
options = {
  'aspirateLowTones': True
}
mstconverter = bp.UnicodeToApi(schema="MST", options = options)

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
    
wordlist_readings = pd.DataFrame({"ipa": homophone_dict.keys(), "nosyl": [findNoSyl(x) for x in homophone_dict.keys()]})


onsets_mst = []
codas_mst = []
nonuc_mst = []
vowels_mst_combined = []
wordlist_ipa_to_parsed = dict()

for word in homophone_dict.keys():
    if not detectNucWordMST(word):
        #If not all syllables have a nucleus
        nonuc_mst = nonuc_mst + [word]
    elif word not in [""]:
        parsed = parseIPAWordMST(word)
        wordlist_ipa_to_parsed[word] = parsed
        for syl in parsed:
            if syl[0] not in onsets_mst:
                onsets_mst = onsets_mst + [syl[0]]
            if syl[1] not in vowels_mst_combined:
                vowels_mst_combined = vowels_mst_combined + [syl[1]]
            if syl[3] not in codas_mst:
                codas_mst = codas_mst + [syl[3]]


segs_mst = list(set(onsets_mst + codas_mst + vowels_mst_combined))
segs_mst.remove("")
segs_mst = segs_mst + ["ʔ"]
seg_feats_list = list(map(lambda x: ipaToFeat(x, features_phoible, features_compo, "segment"), segs_mst))
seg_feats = dict()
for i, seg in enumerate(segs_mst):
    seg_feats[seg] = seg_feats_list[i]
    if seg_feats_list[i] == []:
        print(seg)


dists = getDistsFromFeatureDict(seg_feats)

#Get indel distance
dists_df = pd.DataFrame(dists)
distList = dists_df.values.flatten().tolist()
indelDist = sum(distList) / len(distList) / 2

noSegs = len(dists)
dists["0"] = dict()
for seg in dists:
    dists[seg]["0"] = indelDist
    dists["0"][seg] = indelDist
dists["0"]["0"] = 0

dists_df = pd.DataFrame(dists)

#Exports
dists_df.to_csv("data/mst_dists.csv")
wordlist_readings.to_csv("data/wordlist_readings_nosyl.csv")
with open('data/wordlist_ipa_to_parsed.json', 'w') as f:
    json.dump(wordlist_ipa_to_parsed, f)
with open('data/homophone_dict.json', 'w') as f:
    json.dump(homophone_dict, f)


