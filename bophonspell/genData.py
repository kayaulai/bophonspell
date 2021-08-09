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

#From shadowtalker: https://stackoverflow.com/questions/21292552/equivalent-of-paste-r-to-python
from functools import reduce

def _reduce_concat(x, sep=""):
    return reduce(lambda x, y: str(x) + sep + str(y), x)
        
def paste(*lists, sep=" ", collapse=None):
    result = map(lambda x: _reduce_concat(x, sep=sep), zip(*lists))
    if collapse is not None:
        return _reduce_concat(result, sep=collapse)
    return list(result)


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
    print(word)
    return [parseIPASylMST(syl) for syl in word.split(".")]
        
def detectNucWordMST(word):
    return all([re.search(getListRE(vowels_mst) + "+" + getListRE(vowel_diac_mst) + "*", syl) is not None for syl in word.split(".")])
    
    
def getListRE(options):
    return "[" + "|".join(options) + "]"

def findNoSyl(ipa):
    return len(re.findall("\.", ipa)) + 1
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

devoice_cor = {'g̊': 'k', 'ɟ̊': 'c', 'ɖ̥': 'ʈ', 'd̥': 't', 'b̥': 'p', 'd͡z̥': 'dz'}

def ipaToFeat(ipa, segTable, compTable, fieldname = "segment"):
    seg = ipa
    vec = getVecFromFeatureTable(seg, segTable, fieldname)
    if(vec == []):
        for dev in devoice_cor.keys():
            seg = seg.replace(dev, devoice_cor[dev])
        seg = seg.replace("g", "ɡ")
        seg = seg.replace("͡", "")
        seg = seg.replace("̊", " ̥")
        vec = getVecFromFeatureTable(seg, segTable, fieldname)
    
    if(vec == []):
        diacs = [" ̥", "̃", "̚", "ʰ"]
        curr_diacs = []
        diac_vecs = []
        for diac in diacs:
            if diac in seg:
                seg = seg.replace(diac, "")
                curr_diacs = curr_diacs + diacs
                diac_vecs = diac_vecs + [getVecFromFeatureTable(seg, compTable, fieldname)]
                
        base_vec = getVecFromFeatureTable(seg, segTable, fieldname)
        vec = combine_vecs(base_vec, diac_vecs)
        
    return vec

def getVecFromFeatureTable(ipa, featTable, fieldname = "segment"):
    return featTable[featTable[fieldname] == ipa].drop(fieldname, axis=1).values.flatten().tolist()

def combine_vecs(base_vec, diac_vecs):
    vec = base_vec
    for diac_vec in diac_vecs:
        for i in range(1, len(diac_vecs)):
            if diac_vec[i] != "0":
                vec[i] = diac_vec[i]
    return vec


segs_mst = list(set(onsets_mst + codas_mst + vowels_mst_combined))
segs_mst.remove("")
segs_mst = segs_mst + ["ʔ"]
seg_feats_list = list(map(lambda x: ipaToFeat(x, features_phoible, features_compo, "segment"), segs_mst))
seg_feats = dict()
for i, seg in enumerate(segs_mst):
    seg_feats[seg] = seg_feats_list[i]
    if seg_feats_list[i] == []:
        print(seg)

            
            
def getDistFromVecs(vec1, vec2):
    diff = 0
    for i in range(1, len(vec1)):
        diff += (abs(featValToNum(vec1[i]) - featValToNum(vec2[i])))
    return diff / len(vec1)
    
def featValToNum(val):
    num = 0
    if val == "+":
        num = .5
    elif val == "-":
        num = -.5
    return num

def getDistsFromFeatureDict(featureDict):
    dists = dict()
    for seg1 in featureDict.keys():
        dists[seg1] = dict()
        for seg2 in featureDict.keys():
            #print("Distance between: " + seg1 + " and " + seg2)
            dists[seg1][seg2] = getDistFromVecs(featureDict[seg1], featureDict[seg2])
            #Dealing with unreleased vs glottal stop
            if "̚" in seg1:
                if "̚" in seg2:
                    dists[seg1][seg2] = dists[seg1][seg2] / 2
                else:
                    altDist = getDistFromVecs(featureDict["ʔ"], featureDict[seg2])
                    dists[seg1][seg2] = (dists[seg1][seg2] + altDist) / 2
            elif "̚" in seg2:
                altDist = getDistFromVecs(featureDict["ʔ"], featureDict[seg2])
                dists[seg1][seg2] = (dists[seg1][seg2] + altDist) / 2
                
    return dists

dists = getDistsFromFeatureDict(seg_feats)

#Get indel distance
dists_df = pd.DataFrame(dists)
distList = dists_df.values.flatten().tolist()
indelDist = sum(distList) / len(distList) / 2

noSegs = len(dists)
dists[""] = dict()
for seg in dists:
    dists[seg][""] = indelDist
    dists[""][seg] = indelDist
dists[""][""] = 0

dists_df = pd.DataFrame(dists)

#Exports
dists_df.to_csv("data/mst_dists.csv")
wordlist_readings.to_csv("data/wordlist_readings_nosyl.csv")
with open('data/wordlist_ipa_to_parsed.json', 'w') as f:
    json.dump(wordlist_ipa_to_parsed, f)
with open('data/homophone_dict.json', 'w') as f:
    json.dump(homophone_dict, f)


