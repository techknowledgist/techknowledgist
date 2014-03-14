"""

Takes a file with terms (one term per line) and looks up the technology scores
or the maturity for the term for the years listed in the YEARS global variable.

Usage:

    $ python lookup_scores.py --technology INPUT_FILE OUTPUT_FILE
    $ python lookup_scores.py --maturity INPUT_FILE OUTPUT_FILE

The OUTPUT_FILE will have a column for each technology/maturity score and a
column for the term. If no score was found the value -1 will be used. Scores are
available from 1997 through 2007.

Script behaviour can be changed by editing three global variables:

    YEAR = LIST -- a list of years to process, available are 1997-2007, which is
       the default

    TIME_SERIES_DIR = PATH -- the directory where the time series live, it is
       assumed that within this directory the technology scores live in the
       technology-scores directory and that the maturity scores live in the
       maturity-scores directory

    USE_QUOTES = True|False -- In some cases the input file has the terms
       surrounded by double quotes, set this to True in those cases. The default
       is to not expect quotes.

An example input file is at:
    /home/j/anick/temp/fuse/freq_sc_1997_2003_Agt10.shared_terms

Note that the script loads the entire scores file into memory, which makes the
technology score lookup slow. A faster version would use some kind of database
created from those score file. It takes about 10 seconds for each technology
scores file to load.

"""


import os, sys, codecs


### Edit the following to change script behaviour

YEARS = range(1997, 2008)

TIME_SERIES_DIR = '/home/j/corpuswork/fuse/FUSEData/corpora/ln-cs-500k/time-series/'
TIME_SERIES_DIR = '/home/j/corpuswork/fuse/FUSEData/corpora/ln-us-all-600k/time-series-v2/'

USE_QUOTES = False


### No edits needed after this

TECHNOLOGY_SCORES_DIR = TIME_SERIES_DIR + '/technology-scores'
MATURITY_SCORES_DIR = TIME_SERIES_DIR + '/maturity-scores'

USE_TECHNOLOGY = False
USE_MATURITY = False


def read_input(input_file):
    with codecs.open(input_file) as input_fh:
        list = []
        dict = {}
        for line in input_fh:
            term = line.strip()
            list.append(term)
            dict[term] = [None for x in range(len(YEARS))]
        print "Read", len(dict), "terms from", input_file 
        return list, dict

def read_year_scores(year_file):
    with codecs.open(year_file) as input_fh:
        print "Reading", year_file
        dict = {}
        count = 0
        for line in input_fh:
            count += 1
            #if count > 100000: break
            (term, score) = line.rstrip("\n\r").split("\t")
            dict[term] = score
        return dict

def print_scored_terms(terms, term_idx, output_file):
    print "Writing to", output_file
    with codecs.open(output_file, 'w') as out_fh:
        for term in terms:
            scores = [normalize_score(s) for s in term_idx[term]]
            out_fh.write("%s\t%s\n" % ("\t".join(scores), term))

def normalize_score(score):
    return '-1' if score == '-1' else "%.4f" % float(score)



if __name__ == '__main__':

    if sys.argv[1] == '--technology': USE_TECHNOLOGY = True
    elif sys.argv[1] == '--maturity': USE_MATURITY = True
    input_file = sys.argv[2]
    output_file = sys.argv[3]
    
    terms, term_idx = read_input(input_file)

    DIR =  MATURITY_SCORES_DIR if USE_MATURITY else TECHNOLOGY_SCORES_DIR
    for i in range(len(YEARS)):
        tech_file = os.path.join(DIR, "%d.tab" % YEARS[i])
        if USE_MATURITY:
            tech_file = os.path.join(DIR, "maturity-match-based-%d.txt" % YEARS[i])
        tech_scores = read_year_scores(tech_file)
        for term in terms:
            lookup = term
            if USE_QUOTES:
                lookup = term.strip('"')
            score = tech_scores.get(lookup, '-1')
            term_idx[term][i] = score

    print_scored_terms(terms, term_idx, output_file)
