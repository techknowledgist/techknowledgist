"""

"""

import os, sys, codecs

# path to the corpus directory
CORPUS_DIR = '/home/j/corpuswork/fuse/FUSEData/corpora/ln-us-all-600k'

# name of the time series directory in the corpus directory
TIME_SERIES = 'time-series-v2/maturity-scores'


def read_scores(y1, y2):
    scores = {}
    f1 = os.path.join(CORPUS_DIR, TIME_SERIES, "maturity-match-based-%s.txt" % y1)
    f2 = os.path.join(CORPUS_DIR, TIME_SERIES, "maturity-match-based-%s.txt" % y2)
    fh1 = codecs.open(f1, encoding='utf8')
    fh2 = codecs.open(f2, encoding='utf8')
    maxcount = 50000
    maxcount = sys.maxint
    print f1
    count = 0
    for line in fh1:
        count += 1
        if count > maxcount: break
        term, score = line.rstrip().split("\t")
        scores[term] = [float(score)]
    print f2
    count = 0
    for line in fh2:
        count += 1
        if count > maxcount: break
        term, score = line.rstrip().split("\t")
        scores[term].append(float(score))
    return scores

def analyze_scores(scores, fh):
    for term in scores.keys():
        s1, s2 = scores[term]
        if s1 > 0 and s2 > 0.1 and s2 > (3 * s1):
            fh.write("%.4f\t%.4f\t%.4f\t%s\n" % (s1, s2, s2 - s1, term))

        
if __name__ == '__main__':

    start_year = sys.argv[1]
    end_year = sys.argv[2]
    out = codecs.open("trends-%s-%s.txt" % (start_year, end_year),
                      'w', encoding='utf8')
    
    scores = read_scores(start_year, end_year)
    analyze_scores(scores, out)
