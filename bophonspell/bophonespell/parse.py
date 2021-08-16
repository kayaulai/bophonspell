# -*- coding: utf-8 -*-
"""
Created on Mon Aug 16 02:13:05 2021

@author: User
"""

from utils import paste, getListRE
import re
import pandas as pd


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

#Accepts PARSED syllables as input (i.e. vector with four components)
#For non-tonal varieties, leave third component blank
#zeroInitialAsGlottal = treat initial zeroes as glottal stops, rather than indel
#finalRTDivisor = How much to divide when there is final r/l vs no coda

def findNoSyl(ipa):
    return len(re.findall("\.", ipa)) + 1

