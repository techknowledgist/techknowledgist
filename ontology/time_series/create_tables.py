"""

Take usage and maturity data and create filtered time series for the most
frequent terms. Relies on a time series directory with technology-scores and
maturity-scores subdirectories and a file terms-0025.txt.

Usage:

    $ python create_tables.py
    
Creates a couple of files that can be imported into a database:

    out-years.txt
    out-fscores.txt
    out-ascores.txt
    out-tscores.txt
    out-mscores.txt

The first is for informational purposes and may have no use at all, the other
two can be imported into a database.

It may be a good idea to split this script and let it just create, for example,
maturity scores. That way, we won't need to read and all data when we add a new
time series. Bu tnote that all time series require the technology scores to be
read because of the requirement that at least for one year we have a score
larger than 0.5. The latter could of course be compiled out into a file (like
terms-0025.txt, but then something like terms-tech.txt).

"""


import os, sys, codecs, math

from utils import filter_term_en, filter_term


sys.path.append(os.path.abspath('../..'))
from ontology.utils.file import open_input_file

YEARS = range(1995, 2013 + 1)
#YEARS = range(1995, 1996 + 1)

YEAR_STRINGS = ["%s" % y for y in YEARS]

TIME_SERIES = '/home/j/corpuswork/fuse/FUSEData/corpora/ln-us-all-600k/time-series-v4'
TERMS_FILE = os.path.join(TIME_SERIES, 'terms-0025.txt')




def initialize_terms():
    """Initialize the terms dictionary using frequent terms."""
    terms = {}
    c = 0
    for line in codecs.open(TERMS_FILE, encoding='utf8'):
        c += 1
        #if c > 10: break
        term = line.strip()
        if not filter_term(term, 'en'):
            terms[term] = { 'tscores': dict.fromkeys(YEAR_STRINGS, None),
                            'fscores': dict.fromkeys(YEAR_STRINGS, 0),
                            'ascores': dict.fromkeys(YEAR_STRINGS, 0),
                            'mscores': dict.fromkeys(YEAR_STRINGS, 0) }
    return terms

def add_fscores(terms):
    for year in YEARS:
        fname = os.path.join(TIME_SERIES, 'frequencies',
                             "raw-%d.txt" % year)
        add_scores(terms, fname, year, 'fscores')

def add_tscores(terms):
    for year in YEARS:
        fname = os.path.join(TIME_SERIES, 'technology-scores', "%d.tab" % year)
        add_scores(terms, fname, year, 'tscores')

def add_mscores(terms):
    for year in YEARS:
        fname = os.path.join(TIME_SERIES, 'maturity-scores',
                             "maturity-match-based-%d.txt" % year)
        add_scores(terms, fname, year, 'mscores')

def add_scores(terms, fname, year, scoretype):
    print fname
    fh = open_input_file(fname)
    c = 0
    for line in fh:
        c += 1
        #if c > 100000: break
        if c % 100000 == 0: print c
        term, score = line.rstrip().split("\t")
        if terms.has_key(term):
            terms[term][scoretype][str(year)] = float(score)

def remove_non_technologies(terms):
    keys = terms.keys()
    for term in keys:
        tscores = terms[term]['tscores'].values()
        if max(tscores) < 0.5:
            del terms[term]

def add_ascores(terms):
    """Calculate adjusted frequency scores from the raw frequencies."""
    for year in YEAR_STRINGS:
        scores = []
        for term in terms.keys():
            scores.append(terms[term]['fscores'][year])
        maxscore = max(scores)
        for term in terms.keys():
            fscore = terms[term]['fscores'][year]
            ascore = None
            if fscore is not None:
                ascore = math.log(fscore + 1) / math.log(maxscore + 1)
            terms[term]['ascores'][year] = ascore

def print_terms(terms):
    fh_years = codecs.open('out-years.txt', 'w', encoding='utf8')
    fh_fscores = codecs.open('out-fscores.txt', 'w', encoding='utf8')
    fh_ascores = codecs.open('out-ascores.txt', 'w', encoding='utf8')
    fh_tscores = codecs.open('out-tscores.txt', 'w', encoding='utf8')
    fh_mscores = codecs.open('out-mscores.txt', 'w', encoding='utf8')
    fh_years.write("%s\n" % "\t".join(YEAR_STRINGS))
    c = 0
    for term in terms:
        c += 1
        if c % 10000 == 0: print c
        for year in sorted(terms[term]['fscores'].keys()):
            fscore = terms[term]['fscores'][year]
            #fscore = 'None' if fscore is None else "%d" % fscore
            fh_fscores.write("%d\t" % fscore)
        fh_fscores.write("%s\n" % term)
        print_term(terms, term, year, 'ascores', fh_ascores)
        print_term(terms, term, year, 'tscores', fh_tscores)
        print_term(terms, term, year, 'mscores', fh_mscores)

def print_term(terms, term, year, scoretype, fh):
    for year in sorted(terms[term][scoretype].keys()):
        score = terms[term][scoretype][year]
        score = 'None' if score is None else "%.2f" % score
        fh.write("%s\t" % score)
    fh.write("%s\n" % term)


if __name__ == '__main__':

    print "Initializing terms from frequent terms..."
    terms = initialize_terms()
    print len(terms)

    print "Adding tscores..."
    add_tscores(terms)

    print "Remove non-technologies..."
    remove_non_technologies(terms)
    print len(terms)

    print "Adding fscores..."
    add_fscores(terms)
    
    print "Adding adjusted fscores..."
    add_ascores(terms)
    
    print "Adding mscores..."
    add_mscores(terms)

    print "Printing terms..."
    print_terms(terms)
