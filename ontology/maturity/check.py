"""

Compares the terms in the match results to those in the technology classifier
results or the usage file. 

Usage:

    $ python check.py --overlap-maturity-tscores YYYY
    $ python check.py --overlap-maturity-usage YYYY

    The second argument is a year from 1995 through 2013.

The first invocation tests whether terms in the matches file occur in the
tscores file and the second whether terms in the matches file occur in the usage
file and whether the counts are the same.

All terms in the matches file should be in the tscores and usage files and the
number of matches should be the same.
    
NOTE. This was tested on 1995 and it was almost the case that terms with matches
were a subset of terms with technology scores. There were 19 terms with matches
that did not have a tscore. This is out of 130,866 terms with matches (and there
are 1,388,905 terms with tscores). The same held true for the usage file. But
oddly the actual matches in the usage file are not the same as the ones in the
maturity file, with a large majority set to 0 in the usage file.

The directories are hard-wired below.

"""


import sys, codecs

CORPUS = '/home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k'
CLASSIFICATIONS = CORPUS + '/classifications/technologies-201502'
MATURITY_SUBPATH = 'data/o2_matcher/maturity'

TERM_OVERLAP_FILE = "terms-overlap-tscores-maturity.txt"
USAGE_OVERLAP_FILE = "terms-overlap-usage-maturity.txt"


def read_tscores(tscores_file):
    print 'Reading', tscores_file
    tscores = {}
    c = 0
    for line in codecs.open(tscores_file, encoding='utf-8'):
        c += 1
        #if c > 10000: break
        if c % 100000 == 0: print "%dk" % (c/1000,),
        term, score, doc_count, min, max = line.rstrip("\n\r\f").split("\t")
        tscores[term] = score
    printd
    return tscores

def read_matcher_results(matches_file):
    print "Reading", matches_file
    term_matches = {}
    for line in codecs.open(matches_file, encoding='utf-8'):
        fields = line.split()
        matches = fields[0]
        term = ' '.join(fields[1:])
        term_matches[term] = matches
    print 'number of terms with matches', len(term_matches)
    return term_matches

def read_usage_scores(usage_file):
    print 'Reading', usage_file
    usage = {}
    c = 0
    for line in codecs.open(usage_file, encoding='utf-8'):
        c += 1
        #if c > 10000: break
        if c % 100000 == 0: print "%dk" % (c/1000,),
        if line.startswith('#'): continue
        tscore, uscore, count, matches, term = line.rstrip("\n\r\f").split("\t")
        usage[term] = matches
    print
    return usage

def check_overlap_tscores(tscores_file, matches_file):
    tscores = read_tscores(tscores_file)
    matches = read_matcher_results(matches_file)
    fh = codecs.open(TERM_OVERLAP_FILE, 'w', encoding='utf-8')
    for term in sorted(matches.keys()):
        marker = '+' if term in tscores else '-'
        fh.write("%s\t%s\n" % (marker, term))

def check_overlap_usage(usage_file, matches_file):
    usage = read_usage_scores(usage_file)
    matches = read_matcher_results(matches_file)
    fh = codecs.open(USAGE_OVERLAP_FILE, 'w', encoding='utf-8')
    for term in sorted(matches.keys()):
        mval = matches[term]
        uval = usage.get(term, -1)
        marker = '+' if term in usage else '-'
        fh.write("%s\t%s\t%s\t%s\n" % (marker, mval, uval, term))


if __name__ == '__main__':

    mode = sys.argv[1]
    year = sys.argv[2]
    
    tscores_file = "%s/%s/classify.MaxEnt.out.s4.scores.sum.az" % (CLASSIFICATIONS, year)
    matches_file = "%s/subcorpora/%s/%s/match.results.summ.txt" % (CORPUS, year, MATURITY_SUBPATH)
    usage_file = "usage-%s.txt" % year
    
    if mode == '--overlap-maturity-tscores':
        check_overlap_tscores(tscores_file, matches_file)
        
    if mode == '--overlap-maturity-usage':
        check_overlap_usage(usage_file, matches_file)
