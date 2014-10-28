"""

Generate maturity time series for terms.

Runs on the results of the classifier and the patterns matcher. Creates a series
of tab-separated files that were created in September 2013 as input to the BAE
system. These files could also be input to the ontology.

Usage:

    $ python maturity.py

    No command line arguments, but the following global variables may need to be
    edited: CORPUS_DIR, CLASS_SUBDIR and TIME_SERIES. See the text just under
    'USER SETTINGS' for short explanations and some examples.

Note that for this to work, you need three kinds of input:

    1- files with classification results for each subcorpus, needed is the
       classify.MaxEnt.out.s3.scores.sum file which was created with
       ../classifier/run_iclassifier.py.

    2- results from the matcher in match.results.summ.txt

    3- the list of bad terms, created with ../classifier/utils/filter.py,
       expected to be in the subdirectories of the classifications directory

    4- the list with terms with frequency > 25, created with merge.py and
       split_terms_on_frequency.py, both in ../classifier/utils, expected to be
       in the classifications directory

For each year, there are two tab-separated file with term to maturity score
mappings. The files are named maturity-freq-based-YEAR.txt and
maturity-match-based-YEAR.txt These files are created with maturity.py and
split-maturity-scores.py in patent-classifier/ontology/matcher. Each file has a
term-score pair where the score is the score for that term in the year as
indicated in the filename.

The first file has the same scores as given in phase 1, where each term-year
pair got a 0, 1, or 2 (unavailable, immature, mature). These scores are based on
frequency counts only and are a fallback.

The second file has a score between 0 and 1 for each term-year. These scores are
based on the results of the pattern matcher and are calcualted as follows:

1- Get the rough count of matches for each term for each year.

2- Adjust the count relative to the number of patents in the year.

3- Let's call this adjusted count c. Now take log(c+1)/log(highest_count), where
highest_count is the highest number of matches for all term-year pairs in the
corpus. We take log(c+1) to make sure that a count of 0 leads to a 0 score
(log(0+1) is 0) and log(highest_score) to make sure our highest value is 1.

There are also two files which have the entire time series for all terms over
all years:

	maturity-freq-based.txt
	maturity-match-based.txt

There are time series for about 540K terms, being all terms with a frequency of
25 or higher in the corpus. Maturity scores tend to be meaningless below a
certain threshold (although it is not clear what exactly that threshold is).



$ python maturity.py
    --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-us-all-600k
    --output maturity-scores


"""


import os, sys, codecs, math, getopt


### USER SETTINGS

# years to process
YEARS = [1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007]
YEARS = [1997, 1998]

# path to the corpus directory
CORPUS_DIR = '/home/j/corpuswork/fuse/FUSEData/corpora/ln-us-cs-500k'
CORPUS_DIR = '/home/j/corpuswork/fuse/FUSEData/corpora/ln-us-all-600k'
#CORPUS_DIR = '/home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k'

# directory where the classifications of all subcorpora are
CLASS_SUBDIR = 'classifications'
#CLASS_SUBDIR = 'classifications/phase2-eval'

# name of the time series directory in the corpus directory
TIME_SERIES = 'time-series'
TIME_SERIES = 'time-series-v1'
TIME_SERIES = 'time-series-v2'
TIME_SERIES = 'time-series-v3'
TIME_SERIES = 'time-series-tmp'

# This variable needs to be set manually by finding the term-year pair with the
# highest number of matches.  For convenience, this number is printed each time
# this script runs.
# NOTE: this variable was not changed when running this on the us match results
# that excluded pubyears > 2007, but it did not seem to hurt the results.
# TODO: is this actually needed? Can't it be calculated when all data are loaded?
MAX_NUMBER_OF_MATCHES = 90439  # ln-us-cs-500k
MAX_NUMBER_OF_MATCHES = 26542  # ln-us-all-600k, with files.txt
#MAX_NUMBER_OF_MATCHES = 21981  # ln-us-all-600k, with files-2007.txt
#MAX_NUMBER_OF_MATCHES = 7232   # ln-cn-all-600k, with files-2007.txt

# Threshold that determines what the adjusted frequency count has to be to render
# a technology mature or available.
MATURITY_THRESHOLD = 25
AVAILABILITY_THRESHOLD = 10

### NO USER EDITS NEEDED AFTER THIS


if CORPUS_DIR.endswith('ln-us-cs-500k'):
    CLASS_DIR = os.path.join(CORPUS_DIR, CLASS_SUBDIR)
    CLASS_SUFFIX = '-technologies-standard-1000'
    CLASS_FILE = 'classify.MaxEnt.out.s3.scores.sum'
    MATCH_DIR = os.path.join(CORPUS_DIR, 'subcorpora')
    MATCH_SUBDIR = 'data/o2_matcher/batch-01'
    MATCH_FILE = 'match.results.summ.txt'
elif CORPUS_DIR.endswith('ln-us-all-600k'):
    CLASS_DIR = os.path.join(CORPUS_DIR, CLASS_SUBDIR)
    CLASS_PREFIX = 'technologies-ds1000-all-'
    CLASS_FILE = 'classify.MaxEnt.out.s3.scores.sum'
    CLASS_FILE = 'classify.MaxEnt.out.s4.scores.sum.az'
    MATCH_DIR = os.path.join(CORPUS_DIR, 'subcorpora')
    MATCH_SUBDIR = 'data/o2_matcher/maturity'
    if CLASS_SUBDIR == 'classifications/phase2-eval':
        MATCH_SUBDIR = 'data/o2_matcher/maturity-2007'
    MATCH_FILE = 'match.results.summ.txt'
elif CORPUS_DIR.endswith('ln-cn-all-600k'):
    CLASS_DIR = os.path.join(CORPUS_DIR, CLASS_SUBDIR)
    CLASS_PREFIX = 'technologies-ds1000-all-'
    CLASS_FILE = 'classify.MaxEnt.out.s3.scores.sum'
    MATCH_DIR = os.path.join(CORPUS_DIR, 'subcorpora')
    MATCH_SUBDIR = 'data/o2_matcher/maturity'
    if CLASS_SUBDIR == 'classifications/phase2-eval':
        MATCH_SUBDIR = 'data/o2_matcher/maturity-2007'
    MATCH_FILE = 'match.results.summ.txt'

TERMS_FILE = CLASS_DIR + os.sep + 'all_terms.0025.txt'

TIME_SERIES_DIR = os.path.join(CORPUS_DIR, TIME_SERIES, 'maturity-scores')
TIME_SERIES_DIR = '.'


# Variables needed for various adjustments of counts

# Adjusting for the size of a corpus for a year, YEAR_SIZES is derived by taking
# a "wc -l" on the files.txt in the corpus
YEAR_SIZES_CS_500K = {
    1997: 18555, 1998: 19875, 1999: 22254, 2000: 28576, 2001: 57429, 2002: 51058,
    2003: 49212, 2004: 48869, 2005: 46493, 2006: 33290, 2007: 9058 }
YEAR_SIZES_ALL_600K_v1 = {
    1997: 15941, 1998: 15878, 1999: 17412, 2000: 19533, 2001: 36832, 2002: 38482,
    2003: 42439, 2004: 43903, 2005: 44493, 2006: 43412, 2007: 40715 }
YEAR_SIZES_ALL_600K_v2 = {
    1997: 15932, 1998: 15849, 1999: 17317, 2000: 19174, 2001: 36208, 2002: 37080,
    2003: 38961, 2004: 36314, 2005: 29894, 2006: 20513, 2007: 6017 }
YEAR_SIZES_ALL_600K_v3 = {
    1997: 15914, 1998: 18878, 1999: 17412, 2000: 19533, 2001: 36832, 2002: 38482,
    2003: 42439, 2004: 43903, 2005: 44493, 2006: 43412, 2007: 40715, 2008: 35406,
    2009: 27927, 2010: 17412 }
YEAR_SIZES_ALL_600K_cn_v1 = {
    1997: 1, 1998: 1, 1999: 1, 2000: 1, 2001: 1, 2002: 1,
    2003: 1, 2004: 1, 2005: 1, 2006: 1, 2007: 1 }
YEAR_SIZES_ALL_600K_cn_v2 = {
    1997: 11143, 1998: 12387, 1999: 13550, 2000: 16618, 2001: 19450, 2002: 24389,
    2003: 28596, 2004: 29997, 2005: 33344, 2006: 27194, 2007: 5347 }

if os.path.basename(CORPUS_DIR) == "ln-us-cs-500k":
    YEAR_SIZES = YEAR_SIZES_CS_500K
elif os.path.basename(CORPUS_DIR) == "ln-us-all-600k":
    YEAR_SIZES = YEAR_SIZES_ALL_600K_v1
    if CLASS_SUBDIR == 'classifications/phase2-eval':
        YEAR_SIZES = YEAR_SIZES_ALL_600K_v2
    else:
        YEAR_SIZES = YEAR_SIZES_ALL_600K_v3
elif os.path.basename(CORPUS_DIR) == "ln-cn-all-600k":
    YEAR_SIZES = YEAR_SIZES_ALL_600K_cn_v1
    if CLASS_SUBDIR == 'classifications/phase2-eval':
        YEAR_SIZES = YEAR_SIZES_ALL_600K_cn_v2

LARGEST_SIZE = max(YEAR_SIZES.values())

# Adjusting the match score with the upper bound. 
MATCHES_ADJUSTMENT = math.log(MAX_NUMBER_OF_MATCHES)

print 'YEAR_SIZES:', YEAR_SIZES
print 'LARGEST_SIZE:', LARGEST_SIZE
print 'MATCHES_ADJUSTMENT:', MATCHES_ADJUSTMENT


def adjust_count(year):
    year_size = YEAR_SIZES[year]
    return 1 / (float(year_size) / LARGEST_SIZE)

def read_terms():
    """Return a hash with all terms from TERMS_FILE."""
    terms = {}
    for line in codecs.open(TERMS_FILE):
        term = line.rstrip("\n\r").split("\t")[1]
        terms[term] = True
    print "\nRead %d terms from %s" % (len(terms), TERMS_FILE)
    return terms

def read_matches(match_file):
    """Return a hash for match_file, contains the number of matches for all
    terms from the file. The input file is assumed to have all scores for a
    particular year."""
    term_matches = {}
    for line in codecs.open(match_file):
        fields = line.split()
        matches = fields[0]
        term = ' '.join(fields[1:])
        term_matches[term] = matches
    print "   Read match count for %d terms from %s of %s" % \
          (len(term_matches), os.path.basename(match_file), year)
    return term_matches


def calculate_maturity_scores(maturity_data):

    print "Calculating maturity scores...\n"
    
    for term in maturity_data.keys():
        
        previous_freq_based_score = 0
        previous_match_based_score = 0

        for year in YEARS:

            adjustment = adjust_count(year)
            scores = maturity_data[term].get(year, [None, 0, 0])
            freq = adjustment * int(scores[1])
            matches = adjustment * int(scores[2])

            if freq >= MATURITY_THRESHOLD:
                freq_based_score = 2
            elif freq >= AVAILABILITY_THRESHOLD:
                freq_based_score = 1
            else:
                freq_based_score = 0
            if freq_based_score < previous_freq_based_score:
                freq_based_score = previous_freq_based_score
            scores.append(freq_based_score)
                        
            match_based_score = math.log(matches + 1) / MATCHES_ADJUSTMENT
            if match_based_score < previous_match_based_score:
                difference = previous_match_based_score - match_based_score
                match_based_score = previous_match_based_score - (difference / 5)
            if match_based_score > 1:
                match_based_score = 1.0
            scores.append(match_based_score)
            previous_freq_based_score = freq_based_score
            previous_match_based_score = match_based_score

            maturity_data[term][year] = scores



def read_opts():
    options = ['corpus=', 'output=',
               'verbose' ]
    try:
        return getopt.getopt(sys.argv[1:], 'c:o:v', options)
    except getopt.GetoptError as e:
        sys.exit("ERROR: " + str(e))

        

        
if __name__ == '__main__':

    corpus = None
    output = None
    verbose = False

    (opts, args) = read_opts()
    for opt, val in opts:
        if opt in ('-c', '--corpus'): corpus = val
        if opt in ('-o', '--output'): output = val
        if opt in ('-v', '--verbose'): verbose = True

    terms = read_terms()
    maturity_data = {}

    print 'CORPUS_DIR', CORPUS_DIR
    print 'YEARS', YEARS
    print 'YEAR_SIZES', YEAR_SIZES
    print 'CLASS_SUBDIR', CLASS_SUBDIR
    print 'CLASS_DIR', CLASS_DIR
    try:
        CLASS_SUFFIX
        print 'CLASS_SUFFIX', CLASS_SUFFIX
    except NameError:
        pass
    print 'CLASS_FILE', CLASS_FILE
    print 'MATCH_DIR',MATCH_DIR
    print 'MATCH_SUBDIR', MATCH_SUBDIR
    print 'MATCH_FILE', MATCH_FILE
    print 'TIME_SERIES', TIME_SERIES
    
    for year in YEARS:
        print
        print year
        if CORPUS_DIR.endswith('ln-us-cs-500k'):
            tech_file = "%s/%s%s/%s" % (CLASS_DIR, year, CLASS_SUFFIX, CLASS_FILE)
        elif CORPUS_DIR.endswith('ln-us-all-600k'):
            tech_file = "%s/%s%s/%s" % (CLASS_DIR, CLASS_PREFIX, year, CLASS_FILE)
        elif CORPUS_DIR.endswith('ln-cn-all-600k'):
            tech_file = "%s/%s%s/%s" % (CLASS_DIR, CLASS_PREFIX, year, CLASS_FILE)
        else:
            exit(CORPUS_DIR)
        match_file = "%s/%s/%s/%s" % (MATCH_DIR, year, MATCH_SUBDIR, MATCH_FILE)
        print '  ', tech_file
        print '  ', match_file
        term_matches = read_matches(match_file)
        c = 0
        print "   Reading tech file..."
        for line in codecs.open(tech_file):
            c += 1
            if c % 100000 == 0: print '     ', c
            if c > 10000: break
            term, score, doc_count, min, max = line.rstrip("\n\r\f").split("\t")
            #print score, min, max, doc_count, term
            score = float(score)
            doc_count = int(doc_count)
            if terms.has_key(term):
                match_count = term_matches.get(term, 0)
                maturity_data.setdefault(term, {})[year] = [score, doc_count, match_count]

    print "\nList with maturity scores has %d terms\n" % len(maturity_data)

    calculate_maturity_scores(maturity_data)

    print "Writing maturity scores...\n"

    term_list = sorted(maturity_data.keys())
    maturity_file = codecs.open(TIME_SERIES_DIR + os.sep + 'maturity-all.txt', 'w')
    maturity_scores1 = codecs.open(TIME_SERIES_DIR + os.sep + 'maturity-freq-based.txt', 'w')
    maturity_scores2 = codecs.open(TIME_SERIES_DIR + os.sep + 'maturity-match-based.txt', 'w')

    for year in YEARS:
        maturity_scores1.write("%s\t" % year)
        maturity_scores2.write("%s\t" % year)
    maturity_scores1.write("term\n")
    maturity_scores2.write("term\n")
    
    max_matches = 0
    for term in term_list:
        for year in YEARS:
            tscore, doc_count, match_count, mscore1, mscore2 = \
                    maturity_data[term].get(year, (None, 0, 0, 0, 0))
            match_count = int(match_count)
            maturity_file.write("%s\t%d\t%s\t%.2f\n" % (term, year, mscore1, mscore2))
            maturity_scores1.write("%s\t" % mscore1)
            maturity_scores2.write("%.4f\t" % mscore2)
            if match_count > max_matches:
                max_matches = match_count
        maturity_scores1.write("%s\n" % term)
        maturity_scores2.write("%s\n" % term)

    print "Highest number of matches for any term in any year is %d\n" % max_matches
