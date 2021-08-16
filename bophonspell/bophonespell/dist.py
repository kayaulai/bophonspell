# -*- coding: utf-8 -*-
"""
Created on Mon Aug 16 02:15:11 2021

@author: User
"""

def getSylDistanceMST(syl1, syl2, dists, weights = [.4, .2, .2, .2], zeroInitialAsGlottal = True, finalRTDivisor = 2):
    for i, x in enumerate(syl1):
        if x == "":
            syl1[i] = "0"
    for i, x in enumerate(syl2):
        if x == "":
            syl2[i] = "0"
    
    
    if zeroInitialAsGlottal:
        if syl1[0] == "0":
            syl1[0] = "ʔ"
        if syl2[0] == "0":
            syl2[0] = "ʔ"

    onsetDist = dists[syl1[0]][syl2[0]]
    nucDist = dists[syl1[1]][syl2[1]]
    #Tone dist is twice the indel cost
    toneDist = int(syl1[2] != syl2[2]) * dists["0"]["d"] * 2
    codaDist = dists[syl1[3]][syl2[3]]
    
    #r, l, zero should be more similar to each other
    if syl1[3] in ["r", "l", "0"] and syl2[3] in ["r", "l", "0"]:
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