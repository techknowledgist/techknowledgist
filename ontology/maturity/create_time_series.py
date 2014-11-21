
"""

Generate a file with maturity time series given a list of terms and a set of
files with usage scores.

Usage:

    $ python create_time_series.py -t TERMFILE USAGE_FILE+

    TERMFILE is a file with frequent terms, used as a filter. The arguments
    from USAGE_FILE+ contain a list of files with usage data, all created by
    collect_usage_data. Each of these files is assumed to have a year in them,
    which the script uses to order the timeseries.

The script creates two output files, one with a maturity time series based on
usage rates and one with maturity time series based on raw frequencies. The
first of these should be much more useful. The names of the output files are
hard-coded and include a timestamp, for example:

    out-20141120:195652-frequency-based.txt
    out-20141120:195652-usage-based.txt

"""


import sys, re, codecs, getopt, time

YEAR_EXP = re.compile('\d\d\d\d')

# these are filled in by collect_year_sizes() using the corpora from which the
# usage files were collected
YEAR_SIZES = {}
LARGEST_SIZE = 0

# Threshold that determines what the adjusted frequency count has to be to render
# a technology mature or available.
MATURITY_THRESHOLD = 25
AVAILABILITY_THRESHOLD = 10


def process(args, term_freqs):    
    """The main procedure. It collects the filenames and extracts the years from
    them, finds the sizes for all corpora, extracts the usage rates and
    frequencies for all terms and calculates values for the time series."""
    years_fnames = collect_usage_fnames(args)
    collect_year_sizes(years_fnames)
    frequent_terms = read_terms(term_freqs)
    scores = {}
    years = sorted([yf[0] for yf in years_fnames])
    for year, fname in years_fnames:
        print year, fname
        read_scores(frequent_terms, year, fname, scores)
    print_time_series(years, scores)


def collect_year_sizes(years_fnames):
    """Collect the sizes for all corpora and identify the largest corpus. Size
    is based on number of documents."""
    global LARGEST_SIZE
    for year, fname in years_fnames:
        year = int(year)
        fh = codecs.open(fname, encoding='utf8')
        for line in fh:
            if line.startswith("# corpus  = "):
                file_list = line.strip()[12:] + "/config/files.txt"
                year_size = len(open(file_list).readlines())
                print year_size, file_list
                YEAR_SIZES[year] = year_size
                if year_size > LARGEST_SIZE:
                    LARGEST_SIZE = year_size
        fh.close()

def adjust_count(year):
    """Calculate an adjustment for the size of a year so that for example a raw
    frequency of 12 in a small year has a larger impact than a raw frequency of
    12 in a large year."""
    year_size = YEAR_SIZES[int(year)]
    return 1 / (float(year_size) / LARGEST_SIZE)

def extract_year(fname):
    result = YEAR_EXP.search(fname)
    return result.group(0) if result is not None else None

def collect_usage_fnames(args):
    years_fnames = []
    for fname in args:
        year = extract_year(fname)
        if year is None:
            exit("Error: file '%s' has no year string in it" % fname)
        years_fnames.append([year, fname])
    return years_fnames

def read_terms(terms_file):
    """Return a hash with all terms from TERMS_FILE."""
    print "Reading terms from %s" % terms_file
    terms = {}
    for line in codecs.open(terms_file, encoding='utf8'):
        term = line.rstrip("\n\r").split("\t")[1]
        terms[term] = True
    print "Read %d terms" % len(terms)
    return terms

def read_scores(frequent_terms, year, fname, scores):
    header = ''
    for line in codecs.open(fname, encoding='utf8'):
        if line.startswith('#'):
            header += line
        else:
            (tscore, urate, docs, matches, term) = line.strip().split("\t")
            if frequent_terms.has_key(term):
                scores.setdefault(term, {})[year] = [tscore, urate, docs, matches]
    return header

def print_time_series(years, scores):
    timestamp = time.strftime("%Y%m%d:%H%M%S")
    output1 = "out-%s-usage-based.txt" % timestamp
    output2 = "out-%s-frequency-based.txt" % timestamp
    out1 = codecs.open(output1, 'w', encoding='utf8')
    out2 = codecs.open(output2, 'w', encoding='utf8')
    out1.write("%s\n" % "\t".join(years))
    out2.write("%s\n" % "\t".join(years))
    for term in sorted(scores.keys()):
        last_mscore = 0.0
        last_fscore = 0
        for year in years:
            this_mscore = get_usage_score(last_mscore, scores, term, year)
            this_fscore = get_frequency_score(last_fscore, scores, term, year)
            out1.write("%.4f\t" % this_mscore)
            out2.write("%d\t" % this_fscore)
            last_mscore = this_mscore
            last_fscore = this_fscore
        out1.write("%s\n" % term)
        out2.write("%s\n" % term)

def get_usage_score(last_mscore, scores, term, year):
    scores = scores[term].get(year)
    this_mscore = 0.0 if scores is None else float(scores[1])
    # do not allow the usage-based maturity score to go down in lockstep
    # with the usage rate, reduce the rate
    if this_mscore < last_mscore:
        difference = last_mscore - this_mscore
        this_mscore = last_mscore - (difference / 5)
    return this_mscore

def get_frequency_score(last_fscore, scores, term, year):
    scores = scores[term].get(year)
    frequency = 0 if scores is None else int(scores[2])
    adjustment = adjust_count(year)
    frequency = adjustment * frequency
    if frequency >= MATURITY_THRESHOLD:
        this_fscore = 2
    elif frequency >= AVAILABILITY_THRESHOLD:
        this_fscore = 1
    else:
        this_fscore = 0
    # this score never goes down in a time series
    if this_fscore < last_fscore:
        this_fscore = last_fscore
    return this_fscore
    


if __name__ == '__main__':

    options = []
    (opts, args) = getopt.getopt(sys.argv[1:], 't:', options)
    terms = None
    for opt, val in opts:
        if opt == '-t': terms = val
    if terms is None:
        exit("Error: no terms file specified")

    process(args, terms)









