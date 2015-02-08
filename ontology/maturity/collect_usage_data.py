"""

Creates a file with usage information for terms in a corpus, using a set of
matches over the corpus and a classification over the corpus. What it basically
does is to combine information from the classifier output and the matcher output
for the usage/maturity patterns and prepare it for further processing down the
line (maturity scoring and time series).

Usage:

    $ python collect_usage_data.py OPTIONS

    --corpus DIRECTORY - the name/location of the corpus

    --tscores DIRECTORY - a directory created by the technology classifier
      (ontology/classifier/tclassify.py), the script picks out the file
      classify.MaxEnt.out.s4.scores.sum.az; it is the responsibility of the user
      to make sure that the classifier results selected match the corpus

    --output FILE - output file to write the results to.

    --matches DIRECTORY - the name of the matches directory inside the corpus,
      residing in the corpus directory in data/o2_matcher, the script picks out
      the file match.results.summ.txt in DIRECTORY, the default is 'maturity'

    --language (en|cn) - the language, default is to use 'en'

    --limit INTEGER - the maximum number of lines to take from the file with
      technology scores, useful for debugging only, defaults to using all scores

    The first three options are required. For each required option there is a
    short version (-c, -t and -o).

The output is a file with for each term the technology score, the usage rate,
the number of documents the term occurs in and the number of matches for the
term. The file also has a header with information on how it was generated, input
sources and a few counts including total number of terms, total number of
matches, highest match count and highest document count. Terms are filtered,
removing some obvious crap. The total counts do not include the filtered terms
or any data relating to those filtered terms.

Example:

    $ setenv CORPUS /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k
    $ python collect_usage_data.py \
         --corpus $CORPUS/subcorpora/1995 \
         --tscores $CORPUS/classifications/technologies-201502/1995 \
         --output usage-1995.txt \
         --language cn

In the output, terms are presented with four numbers as follows:

    0.0029   0.0000   2   0   accelerometer senses
    1.0000   0.0000   1   0   accelerometer sensor
    0.0555   0.1201   5   2   accelerometer signal
    0.9189   0.0757   1   1   accelerometer signal accel
    0.9656   0.0757   1   1   accelerometer signal trace

The first column has the average technology score for the term in the corpus,
the second the usage rate, the third the number of documents the term occurs in,
and the fourth the number of matches for the term.

The usage rate is calculated as follows:

        log(match_count + 1)
    ----------------------------
    log(highest_match_count + 1)

The result is a numner between 0 and 1. Most terms have zero scores, which
correspond to no matches found (that is, no evidence of usage found). The closer
the number gets to 1, the closer the term usage is relative to the term with the
most matches.

"""

# TODO
#
# - add check that compares files.txt in the corpus and the files used for the
#   classification



import os, sys, getopt, codecs, math

sys.path.append(os.path.abspath('../..'))
from ontology.utils.git import get_git_commit


def create_usage_file(corpus, matches, tscores, output,
                      limit=sys.maxint, language="en"):
    """Creates a file with technology scores, usage scores, document count and
    match count for each term in a corpus."""

    matches_file = os.path.join(corpus, 'data', 'o2_matcher',
                                matches, 'match.results.summ.txt')
    tscores_file = os.path.join(tscores, 'classify.MaxEnt.out.s4.scores.sum.az')
    _print_header(corpus, matches, tscores, language, output)
    term_matches = _read_matches(matches_file)
    stats = TermStats()
    print "Reading technology scores and document counts..."
    c = 0
    for line in codecs.open(tscores_file, encoding='utf-8'):
        c += 1
        if c > limit: break
        if c % 100000 == 0: print "%dk" % (c/1000,),
        term, score, doc_count, min, max = line.rstrip("\n\r\f").split("\t")
        if filter_term(term, language):
            continue
        stats.update(term, score, doc_count, term_matches)
    print "\nCalculating usage rates..."
    calculate_usage_rates(stats)
    print "Writing usage data..."
    fh_out = codecs.open(output, 'w', encoding='utf-8')
    _write_info(fh_out, corpus, matches_file, tscores_file)
    _write_aggregate_counts(fh_out, stats)
    _write_term_data(fh_out, stats.usage_data)


def calculate_usage_rates(stats):
    # in rare circumstances there are no matches, use 1.0001 instead of 1 to
    # avoid a null division error with the adjustment value
    adjustment = math.log(stats.highest_match_count + 1.0001)
    for term in stats.usage_data:
        [tscore, doc_count, match_count] = stats.usage_data[term]
        usage = math.log(match_count + 1) / adjustment
        stats.usage_data[term] = [tscore, usage, doc_count, match_count]

def filter_term(term, language):
    if language == "en": return filter_term_en(term)
    if language == "cn": return filter_term_cn(term)

def filter_term_en(term):
    """Filter out some obvious crap. Do not allow (i) terms with spaces only,
    (ii) terms with three or more hyphens/underscores in a row, (iii) terms
    where half or less of the characters are alphabetical, and (iv) terms that
    are longer than 75 characters. The latter avoids using what could be huge
    outliers."""
    if term.strip() == '' \
       or term.find('---') > -1 \
       or term.find('___') > -1 \
       or len([c for c in term if c.isalpha()]) * 2 < len(term) \
       or len(term) > 75:
        return True
    return False

def filter_term_cn(term):
    return False

def _print_header(corpus, matches, tscores, langauge, output):
    print "\nCreating usage statistics of terms\n"
    print "  corpus   =", corpus
    print "  matches  =", os.path.basename(matches)
    print "  tscores  =", os.path.basename(tscores)
    print "  language =", language
    print "  output   =", output, "\n"

def _write_info(fh, corpus, matches, tscores):
    fh.write("#\n# $ python %s\n#\n" % ' '.join(sys.argv))
    fh.write("# git_commit = %s\n#\n" % get_git_commit())
    fh.write("# corpus  = %s\n" % corpus)
    fh.write("# matches = %s\n" % _condense_path(matches, corpus))
    fh.write("# tscores = %s\n" % _condense_path(tscores, corpus))
    fh.write("#\n")

def _condense_path(path, prefix):
    if path.startswith(prefix):
        return "<corpus>" + path[len(prefix):]
    return path

def _write_aggregate_counts(fh, stats):
    fh.write("# TOTAL_TERMS = %d\n" % stats.total_terms)
    fh.write("# TOTAL_MATCHES = %d\n" % stats.total_matches)
    fh.write("# TOTAL_TERMS_WITH_MATCHES = %d\n" % stats.total_terms_with_matches)
    fh.write("# HIGHEST_MATCH_COUNT = %d\n" % stats.highest_match_count)
    fh.write("# HIGHEST_DOC_COUNT = %d\n#\n" % stats.highest_doc_count)

def _write_term_data(fh, usage_data):
    for term in sorted(usage_data.keys()):
        tscore, uscore, doc_count, match_count = usage_data[term]
        fh.write("%.4f\t%.4f\t%d\t%d\t%s\n" %
                 (tscore, uscore, doc_count, match_count, term))

def _read_matches(match_file):
    """Return a hash for match_file, contains the number of matches for all
    terms from the file. The input file is assumed to have all scores for a
    particular year."""
    print "Reading term matches..."
    term_matches = {}
    for line in codecs.open(match_file, encoding='utf-8'):
        fields = line.split()
        matches = fields[0]
        term = ' '.join(fields[1:])
        term_matches[term] = matches
    return term_matches


class TermStats(object):

    """Convenience object to store and update counters and usage data."""

    def __init__(self):
        self.usage_data = {}
        self.total_terms = 0
        self.total_matches = 0
        self.total_terms_with_matches = 0
        self.highest_match_count = 0
        self.highest_doc_count = 0

    def update(self, term, score, doc_count, term_matches):
        self.total_terms += 1
        score = float(score)
        doc_count = int(doc_count)
        match_count = int(term_matches.get(term, 0))
        if match_count > 0:
            self.total_terms_with_matches += 1
        self.total_matches += match_count
        if match_count > self.highest_match_count:
            self.highest_match_count = match_count
        if doc_count > self.highest_doc_count:
            self.highest_doc_count = doc_count
        self.usage_data[term] = [score, doc_count, match_count]

def check_args(corpus, matches, tscores, output):
    if corpus is None:
        exit("ERROR: no corpus specified with --corpus option")
    elif matches is None:
        exit("ERROR: no matches file specified with --matches option")
    elif tscores is None:
        exit("ERROR: no technology scores file specified with --tscores option")
    elif output is None:
        exit("ERROR: no output file specified with --output option")

        

if __name__ == '__main__':
    
    options = ['output=', 'corpus=', 'matches=', 'tscores=', 'limit=', 'language=']
    (opts, args) = getopt.getopt(sys.argv[1:], 'o:c:t:', options)

    output = None
    corpus = None
    tscores = None
    matches = 'maturity'
    language = "en"
    limit = sys.maxint
    
    for opt, val in opts:
        if opt in ('--output', '-o'): output = val
        elif opt in ('--corpus', '-c'): corpus = val
        elif opt in ('--tscores', '-t'): tscores = val
        elif opt in ('--language'): language = val
        elif opt in ('--matches'): matches = val
        elif opt in ('--limit'): limit = int(val)

    check_args(corpus, matches, tscores, output)
    create_usage_file(corpus, matches, tscores, output, limit, language)
