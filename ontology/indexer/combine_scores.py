"""

Script to combine corpus-level term information from three sources:

    1. frequency summary for the corpus
    2. technology scores for the corpus
    3. maturity scores for the corpus

The first is created by summarize_scores.py, the others come from the time
series. The output is a file named index.terms.txt with four columns: term,
frequency, technology score and maturity score. If no value was found for a
score, then -1 is used.

Usage:
    $ python combine_scores.py OPTIONS

Options:
    --corpus   -  the corpus to run the matcher on
    --batch    -  directory in data/o2_index to read from and write to
    --verbose  -  print progress

Example:
    $ python summarize_frequencies.py \
      --corpus data/patents/201306-computer-science \
      --batch standard \
      --verbose

"""


import os, sys, getopt, codecs

#sys.path.append(os.path.abspath('../..'))
#from ontology.utils.file import open_input_file


# TODO: the entire way of dealing with the aggregate and the sub corpus sucks

AGGREGATE_CORPUS_US = "/home/j/corpuswork/fuse/FUSEData/corpora/ln-us-all-600k"
AGGREGATE_CORPUS_CN = "/home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k"
AGGREGATE_CORPUS = AGGREGATE_CORPUS_CN

TIME_SERIES = "time-series-v2"

# TODO: these two should be on the command line
if AGGREGATE_CORPUS == AGGREGATE_CORPUS_US:
    TECHNOLOGY_SCORES = "technology-scores/2000.tab"
    MATURITY_SCORES = "maturity-scores/maturity-match-based-2000.txt"
else:
    TECHNOLOGY_SCORES = "technology-scores-cn/2000.tab"
    MATURITY_SCORES = "maturity-scores-cn/maturity-match-based-2000.txt"

VERBOSE = False


def combine(corpus, batch):

    batch_dir = os.path.join(corpus, 'data', 'o1_index', batch)
    frequency_file = os.path.join(batch_dir, 'index.locs.summ.az.txt')
    combined_file = os.path.join(batch_dir, 'index.terms.txt')
    technology_scores_file = os.path.join(AGGREGATE_CORPUS, TIME_SERIES, TECHNOLOGY_SCORES)
    maturity_scores_file = os.path.join(AGGREGATE_CORPUS, TIME_SERIES, MATURITY_SCORES)

    fh_freqs = codecs.open(frequency_file, encoding='utf-8')
    fh_technology_scores = codecs.open(technology_scores_file, encoding='utf-8')
    fh_maturity_scores = codecs.open(maturity_scores_file, encoding='utf-8')
    fh_out = codecs.open(combined_file, 'w', encoding='utf-8')

    print frequency_file
    print technology_scores_file
    print maturity_scores_file
    print combined_file

    terms = {}

    count = 0
    if VERBOSE: print "\nReading", frequency_file
    for line in fh_freqs:
        count += 1
        #if count > 100000: break
        if count % 100000 == 0 and VERBOSE: print '  ', count
        (freq, term) = line.rstrip().split("\t")
        terms.setdefault(term, [-1, -1, -1])[0] = freq

    count = 0
    if VERBOSE: print "\nReading",  technology_scores_file
    for line in fh_technology_scores:
        count += 1
        #if count > 100000: break
        if count % 100000 == 0 and VERBOSE: print '  ', count
        (term, score) = line.rstrip().split("\t")
        terms.setdefault(term, [-1, -1, -1])[1] = score

    count = 0
    if VERBOSE: print "\nReading",  maturity_scores_file
    for line in fh_maturity_scores:
        count += 1
        #if count > 100000: break
        if count % 100000 == 0 and VERBOSE: print '  ', count
        (term, score) = line.rstrip().split("\t")
        terms.setdefault(term, [-1, -1, -1])[2] = score

    if VERBOSE: print "\nWriting",  combined_file
    count = 0
    for t, vals in terms.items():
        count += 1
        if count % 100000 == 0 and VERBOSE: print '  ', count
        #print t, vals
        fh_out.write("%s\t%s\t%s\t%s\n" % (t, vals[0], vals[1], vals[2]))


def read_opts():
    longopts = ['corpus=', 'batch=', 'verbose' ]
    try:
        return getopt.getopt(sys.argv[1:], '', longopts)
    except getopt.GetoptError as e:
        sys.exit("ERROR: " + str(e))


if __name__ == '__main__':

    corpus = None
    batch = None

    (opts, args) = read_opts()
    for opt, val in opts:
        if opt == '--corpus': corpus = val
        elif opt == '--batch': batch = val
        elif opt == '--verbose': VERBOSE = True

    combine(corpus, batch)
