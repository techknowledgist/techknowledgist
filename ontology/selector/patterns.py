
import re


patterns_en = {
    
    1: ['r', "\bfield[a-z]*|area[a-z]*", "TERM field|area"],
    2: ['l', "\bintroduce[a-z]*", "introduce TERM"],
    3: ['l', "\bimprove[a-z]*", "improve TERM"],
    4: ['l', "\badvance[a-z]*", "advance TERM"],
    5: ['l', "\bprogress[a-z]*", "progress TERM"],
    6: ['l', "\bnovel[a-z]*", "novel TERM"],
    7: ['l', "\buse[a-z]*|appl[a-z]+", "use|apply TERM"],
    8: ['l', "\bmeans", "means of TERM"],
    9: ['l', "\badvent", "advent of TERM"],
    10: ['r', "\brevolution[a-z]*", "TERM revolution"],
    11: ['r', "\bmethod[a-z]*", "TERM method"],
    12: ['l', "\bpredict[a-z]*", "predict TERM"],
    13: ['r', "\btechnolog[a-z]+", "TERM technology"],
    14: ['r', "\btechnique[a-z]*", "TERM technique"],
    15: ['l', "\bnew", "new TERM"]

    }



patterns_de = {}

patterns_cn = {}


def patterns(language):

    if language == 'en':
        patterns = patterns_en
    elif language == 'cn':
        patterns = patterns_cn
    elif language == 'de':
        patterns = patterns_de

    for p in patterns.values():
        p[1] = re.compile(p[1])

    return patterns
