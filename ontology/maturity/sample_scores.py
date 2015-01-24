"""

Takes a sample of both technology scores and maturity scores, given a range of
years in a time series. Takes samples for terms with hihh scores, medium scores,
low scores and rising scores. For maturity scores a technology filter is used
(the technology score needs to be larger than 0.5). Only terms with scores for
all years are included.

Written to comply with a request for some good examples of scores for
Chinese. 

Edit the five variables on top to set behaviour of the script.

GET_TECHNOLOGIES:
    run this once to collect all technologies mentioned from a time series
    
GET_TSCORES:
    get sample of technology scores from 200K lines of each file
    
GET_MSCORES:
    get sample of maturity scores.
    
SERIES:
    the time series that are input to the sampling
    
YEARS:
    set a range of years

The file with technologies is written to SERIES/all-technologies.txt, sample
output is written to a series of files in the local directory, all matching
out-?scores-*.txt.

TODO: this should probably be in another directory, something like
ontology/data_analysis.

"""

# USER EDITS

GET_TECHNOLOGIES = False
GET_TSCORES = False
GET_MSCORES = True
SERIES = '/home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/time-series-v2'
YEARS = [2001, 2002, 2003, 2004, 2005]

# NO USER EDITS REQUIRED AFTER THIS

import codecs, numpy, random


if GET_TECHNOLOGIES:
    TSCORES_DIR = SERIES + '/technology-scores-cn'
    FH_TECHNOLOGIES = codecs.open(SERIES + "/all-technologies.txt", 'w', encoding='utf8')

if GET_TSCORES:
    TSCORES = {}
    TSCORES_DIR = SERIES + '/technology-scores-cn'
    FH_LOW_TSCORES = codecs.open("out-tscores-low.txt", 'w', encoding='utf8')
    FH_MEDIUM_TSCORES = codecs.open("out-tscores-medium.txt", 'w', encoding='utf8')
    FH_HIGH_TSCORES = codecs.open("out-tscores-high.txt", 'w', encoding='utf8')
    # FH_VARIABLE_TSCORES = codecs.open("out-tscores-variable.txt", 'w', encoding='utf8')
    FH_RISING_TSCORES = codecs.open("out-tscores-rising.txt", 'w', encoding='utf8')

if GET_MSCORES:
    MSCORES = {}
    MSCORES_DIR = SERIES + '/maturity-scores-cn'
    FH_TECHNOLOGIES = codecs.open(SERIES + "/all-technologies.txt", encoding='utf8')
    FH_LOW_MSCORES = codecs.open("out-mscores-low.txt", 'w', encoding='utf8')
    FH_MEDIUM_MSCORES = codecs.open("out-mscores-medium.txt", 'w', encoding='utf8')
    FH_HIGH_MSCORES = codecs.open("out-mscores-high.txt", 'w', encoding='utf8')
    # FH_VARIABLE_MSCORES = codecs.open("out-mscores-variable.txt", 'w', encoding='utf8')
    FH_RISING_MSCORES = codecs.open("out-mscores-rising.txt", 'w', encoding='utf8')

    
def get_technologies():
    technologies = {}
    for year in YEARS:
        tscores = "%s/%d.tab" % (TSCORES_DIR, year)
        print tscores
        c = 0
        for line in codecs.open(tscores, encoding='utf8'):
            c += 1
            if c % 100000 == 0: print c
            #if c > 100000: break
            (term, score) = line.rstrip().split("\t")
            if float(score) > 0.5 and is_chinese(term):
                technologies[term] =  True
    for term in technologies:
        FH_TECHNOLOGIES.write("%s\n" % term)

def read_technologies():
    print "reading technologies..."
    technologies = {}
    for line in FH_TECHNOLOGIES:
        technologies[line.strip()] = True
    return technologies

def read_tscores():
    for year in YEARS:
        tscores = "%s/%d.tab" % (TSCORES_DIR, year)
        print tscores
        c = 0
        for line in codecs.open(tscores, encoding='utf8'):
            c += 1
            if c % 100000 == 0: print c
            if c > 200000: break
            (term, score) = line.rstrip().split("\t")
            if is_chinese(term):
                TSCORES.setdefault(term, {})
                TSCORES[term][year] = float(score)

def read_mscores():
    for year in YEARS:
        mscores = "%s/maturity-match-based-%d.txt" % (MSCORES_DIR, year)
        print mscores
        for line in codecs.open(mscores, encoding='utf8'):
            (term, score) = line.rstrip().split("\t")
            if is_chinese(term):
                MSCORES.setdefault(term, {})
                MSCORES[term][year] = float(score)

def is_chinese(term):
    for c in term:
        if c.isspace():
            continue
        if c < u'\u4e00' or c > u'\u9fa5':
            return False
    return True
        
def print_scores(fh, scores_list):
    random.shuffle(scores_list)
    for term, scores in scores_list:
        print_term_scores(fh, term, scores)

def print_term_scores(fh, term, scores):
    fh.write("%s\t%s\n" % ("\t".join(["%.2f" % s for s in scores]), term))

def find_tscores():
    scores_low = []
    scores_medium = []
    scores_high = []
    scores_rising = []
    scores_variable = []
    for term, scores in TSCORES.items():
        if len(scores) < 5:
            continue
        scores_list = [scores[year] for year in sorted(scores.keys())]
        ssum = sum(scores_list)
        stdev = numpy.std(scores_list)
        rising = scores_list[-1] > scores_list[0] + 0.2
        if 0.5 < ssum < 1: scores_low.append([term, scores_list])
        if 2.25 < ssum < 2.75: scores_medium.append([term, scores_list])
        if 4.5 < ssum < 4.9: scores_high.append([term, scores_list])
        if stdev > 0.03: scores_variable.append([term, scores_list])
        if stdev > 0.02 and rising: scores_rising.append([term, scores_list])
    print_scores(FH_LOW_TSCORES, scores_low)
    print_scores(FH_MEDIUM_TSCORES, scores_medium)
    print_scores(FH_HIGH_TSCORES, scores_high)
    #print_scores(FH_VARIABLE_TSCORES, scores_variable)
    print_scores(FH_RISING_TSCORES, scores_rising)

def find_mscores():
    technologies = read_technologies()
    scores_low = []
    scores_medium = []
    scores_high = []
    scores_rising = []
    scores_variable = []
    for term, scores in MSCORES.items():
        if not term in technologies: continue
        if len(scores) < 5: continue
        scores_list = [scores[year] for year in sorted(scores.keys())]
        ssum = sum(scores_list)
        stdev = numpy.std(scores_list)
        rising = scores_list[-1] > scores_list[0] + 0.25
        if 0.1 < ssum < 0.3: scores_low.append([term, scores_list])
        if 2.0 < ssum < 2.25: scores_medium.append([term, scores_list])
        if 2.5 < ssum: scores_high.append([term, scores_list])
        if stdev > 0.03: scores_variable.append([term, scores_list])
        if stdev > 0.02 and rising: scores_rising.append([term, scores_list])
    print_scores(FH_LOW_MSCORES, scores_low)
    print_scores(FH_MEDIUM_MSCORES, scores_medium)
    print_scores(FH_HIGH_MSCORES, scores_high)
    #print_scores(FH_VARIABLE_MSCORES, scores_variable)
    print_scores(FH_RISING_MSCORES, scores_rising)


if __name__ == '__main__':

    if GET_TECHNOLOGIES:
        get_technologies()

    if GET_TSCORES:
        read_tscores()
        find_tscores()

    if GET_MSCORES:
        read_mscores()
        find_mscores()
