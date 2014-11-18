
"""

Generate a file with maturity time series given a list of terms and a set of
files with usage scores.

Usage:

    $ python create_time_series.py -t TERMFILE -o OUTPUTFILE USAGE_FILE+

    -t TERMFILE  -  a file with frequent terms, used as a filter
    -o OUTPUT  - file to write the output to

    The arguments USAGE_FILE+ contain a list of files with usage data, all
    created by collect_usage_data. Each of these files is assumed to have a year
    in them, which the script uses to order the timeseries.

"""

# TODO:
#
# - this only creates the full file with all years and all scores, also create
#   the files for individual years (do this with a separate script)
#
# - add the frequency-based scores


import sys, re, codecs, getopt


YEAR_EXP = re.compile('\d\d\d\d')



def process(term_freqs, years_fnames, output):
    frequent_terms = read_terms(term_freqs)
    scores = {}
    years = sorted([yf[0] for yf in years_fnames])
    for year, fname in years_fnames:
        print year, fname
        read_scores(frequent_terms, year, fname, scores)
    print_time_series(years, scores, output)

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

def print_time_series(years, scores, output):
    out = codecs.open(output, 'w', encoding='utf8')
    out.write("%s\n" % "\t".join(years))
    for term in sorted(scores.keys()):
        last_score = 0.0
        for year in years:
            this_score = get_usage_score(scores, term, year)
            # do not allow the maturity score to go down in lockstep with the
            # usage rate
            if this_score < last_score:
                difference = last_score - this_score
                this_score = last_score - (difference / 5)
            out.write("%.4f\t" % this_score)
            last_score = this_score
        out.write("%s\n" % term)

def get_usage_score(scores, term, year):
    scores = scores[term].get(year)
    if scores is None:
        score = 0.0
    else:
        score = float(scores[1])
    return score



if __name__ == '__main__':

    options = ['output=', 'terms=']
    (opts, args) = getopt.getopt(sys.argv[1:], 'o:t:', options)
    output = None
    terms = None
    for opt, val in opts:
        if opt == '-o': output = val
        if opt == '-t': terms = val
    years_fnames = collect_usage_fnames(args)
    if output is None:
        exit("Error: no output file specified")
    if terms is None:
        exit("Error: no terms file specified")
    process(terms, years_fnames, output)









