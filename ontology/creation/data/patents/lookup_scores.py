"""

Takes a file with terms (one term per line) and looks up the technology scores
for the term for the years listed in the YEARS global variable.

Usage:

    $ python lookup_scores.py INPUT_FILE OUTPUT_FILE

The OUTPUT_FILE will have a column for each technology score and a column for
the term. If no score was found the value -1 will be used. Scores are available
from 1997 through 2007. By default, the scores for 1997 and 2003 are looked
up. Change the value of YEARS below to change this.

An example input file is at:
    /home/j/anick/temp/fuse/freq_sc_1997_2003_Agt10.shared_terms

Note that the script loads the entire scores file into memory, a faster version
would use some kind of database created from those score file. It takes about 10
seconds for each scores file to load.

"""


import os, sys, codecs


YEARS = [1997, 2003]

TIME_SERIES_DIR = '/home/j/corpuswork/fuse/FUSEData/corpora/ln-cs-500k/time-series/technology-scores'



def read_input(input_file):
    with codecs.open(input_file) as input_fh:
        dict = {}
        for line in input_fh:
            dict[line.strip()] = [None for x in range(len(YEARS))]
        print "Read", len(dict), "terms from", input_file 
        return dict

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

def print_scored_terms(terms, output_file):
    print "Writing to", output_file
    with codecs.open(output_file, 'w') as out_fh:
        for term in sorted(terms.keys()):
            scores = terms[term]
            #if [x for x in scores if x != '-1']: print scores, term
            out_fh.write("%s\t%s\n" % ("\t".join(scores), term))


if __name__ == '__main__':

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    terms = read_input(input_file)
    
    for i in range(len(YEARS)):
        tech_file = os.path.join(TIME_SERIES_DIR, "%d.tab" % YEARS[i])
        tech_scores = read_year_scores(tech_file)
        for term in terms.keys():
            score = tech_scores.get(term, '-1')
            terms[term][i] = score

    print_scored_terms(terms, output_file)
