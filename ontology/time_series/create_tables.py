"""

Take usage and maturity data and create filtered time series for the most
frequent terms. Relies on a time series directory with technology-scores and
maturity-scores subdirectories and a file terms-0025.txt. Creates files that can
be imported into the term-browser database.

Usage:

    $ python create_tables.py OPTIONS

    --technology:
        create scores-technology.txt with technology scores

    --maturity:
        create scores-maturity.txt with maturity scores

    --frequency:
        create scores-frequency-raw.txt with document counts
        create scores-frequency-rel.txt with relative frequencies

    --keyterms:
        create scores-keyterms-role-i.txt
        create scores-keyterms-role-ct.txt
        create scores-keyterms-role-ca.txt

    --all:
        create all the above

The input is taken from the time series specified in TIME_SERIES and the value
of TERMS_FILE is taken as a filter on what terms to take.

Files are written to the current working directory. Output files all have the
same format:

    0.00   0.17   0.14   air sensor

First there are len(YEARS) colums with the score, followed by one column with
the term. Columns are tab-separated. The score are floats, except for the raw
frequency files, where they are integers. In some cases the score can be None
(for example, for technology scores when there were no occurrences for the year.

The options above drive what files are written and what input is read, but note
that no matter what options you use the technology time series will always be
read because there are needed for the filter.

"""

TEST = False
#TEST = True

import os, sys, codecs, math, getopt, StringIO
from utils import filter_term_en, filter_term
sys.path.append(os.path.abspath('../..'))
from ontology.utils.file import open_input_file

YEARS = range(1995, 2013 + 1)
if TEST:
    YEARS = range(1995, 1996 + 1)

YEAR_STRINGS = ["%s" % y for y in YEARS]

TIME_SERIES = '/home/j/corpuswork/fuse/FUSEData/corpora/ln-us-all-600k/time-series-v4'
TERMS_FILE = os.path.join(TIME_SERIES, 'terms-0025.txt')



def initialize_terms(mscores, fscores, kscores):
    """Initialize the terms dictionary using frequent terms."""
    print "Initializing terms from frequent terms..."
    terms = {}
    c = 0
    for line in codecs.open(TERMS_FILE, encoding='utf8'):
        c += 1
        if TEST and c > 100000: break
        if c % 100000 == 0: print c
        term = line.strip()
        if not filter_term(term, 'en'):
            terms[term] = { 'tscores': dict.fromkeys(YEAR_STRINGS, None) }
            if mscores:
                terms[term]['mscores'] = dict.fromkeys(YEAR_STRINGS, 0)
            if fscores:
                terms[term]['fscores'] = dict.fromkeys(YEAR_STRINGS, 0)
                terms[term]['ascores'] = dict.fromkeys(YEAR_STRINGS, 0)
            if kscores:
                terms[term]['kf_scores'] = dict.fromkeys(YEAR_STRINGS, 0)
                terms[term]['kct_scores'] = dict.fromkeys(YEAR_STRINGS, 0)
                terms[term]['kca_scores'] = dict.fromkeys(YEAR_STRINGS, 0)
                terms[term]['ki_scores'] = dict.fromkeys(YEAR_STRINGS, 0)
    print "loaded", len(terms), "terms"
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
    print scoretype, fname
    fh = open_input_file(fname)
    c = 0
    for line in fh:
        c += 1
        if TEST and c >= 100000: break
        if c % 100000 == 0: print c
        term, score = line.rstrip().split("\t")
        if terms.has_key(term):
            terms[term][scoretype][str(year)] = float(score)

def remove_non_technologies(terms):
    print "Remove non-technologies..."
    keys = terms.keys()
    for term in keys:
        tscores = terms[term]['tscores'].values()
        if max(tscores) < 0.5:
            del terms[term]
    print "terms remaining:", len(terms)

def add_ascores(terms):
    """Calculate adjusted frequency scores from the raw frequencies."""
    print "Calculating adjusted fscores..."
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

def add_kscores(terms):
    for year in YEAR_STRINGS:
        add_kscores_for_year(terms, 'ki_scores', 'i', year)
        add_kscores_for_year(terms, 'kct_scores', 'ct', year)
        add_kscores_for_year(terms, 'kca_scores', 'ca', year)

def add_kscores_for_year(terms, key, roletype, year):
    fname = os.path.join(TIME_SERIES, 'keyterms', "roles-%s-%s.txt" % (roletype, year))
    print "k%s_scores" % roletype, fname
    fh = open_input_file(fname)
    c = 0
    for line in fh:
        c += 1
        if TEST and c >= 100000: break
        if c % 100000 == 0: print c
        (term, count, ratio) = line.rstrip("\n\f\r").split("\t")
        if terms.has_key(term):
            terms[term]['kf_scores'][year] += int(count)
            terms[term][key][year] = int(count)

def print_terms(terms, tscores, mscores, fscores, kscores):
    print "Printing terms..."
    s_fscores = StringIO.StringIO()
    s_ascores = StringIO.StringIO()
    s_tscores = StringIO.StringIO()
    s_mscores = StringIO.StringIO()
    s_ki_scores = StringIO.StringIO()
    s_kct_scores = StringIO.StringIO()
    s_kca_scores = StringIO.StringIO()
    c = 0
    for term in terms:
        c += 1
        if c % 10000 == 0: print c
        add_term_to_stream(terms, term, 'tscores', s_tscores, tscores, float)
        add_term_to_stream(terms, term, 'mscores', s_mscores, mscores, float)
        add_term_to_stream(terms, term, 'fscores', s_fscores, fscores, int)
        add_term_to_stream(terms, term, 'ascores', s_ascores, fscores, float)
        add_term_to_stream(terms, term, 'ki_scores', s_ki_scores, kscores, int)
        add_term_to_stream(terms, term, 'kct_scores', s_kct_scores, kscores, int)
        add_term_to_stream(terms, term, 'kca_scores', s_kca_scores, kscores, int)
    print_from_stream(s_tscores, 'scores-technologies.txt', tscores)
    print_from_stream(s_mscores, 'scores-maturity.txt', mscores)
    print_from_stream(s_fscores, 'scores-frequencies-raw.txt', fscores)
    print_from_stream(s_ascores, 'scores-frequencies-rel.txt', fscores)
    print_from_stream(s_ki_scores, 'scores-keyterms-role-i.txt', kscores)
    print_from_stream(s_kct_scores, 'scores-keyterms-role-ct.txt', kscores)
    print_from_stream(s_kca_scores, 'scores-keyterms-role-ca.txt', kscores)

def add_term_to_stream(terms, term, scoretype, fh, scores_p, valuetype):
    if not scores_p:
        return
    if valuetype is float:
        add_term_to_stream_using_float(terms, term, scoretype, fh)
    elif valuetype is int:
        add_term_to_stream_using_int(terms, term, scoretype, fh)

def add_term_to_stream_using_float(terms, term, scoretype, fh):
    for year in sorted(terms[term][scoretype].keys()):
        score = terms[term][scoretype][year]
        score = 'None' if score is None else "%.2f" % score
        fh.write("%s\t" % score)
    fh.write("%s\n" % term)

def add_term_to_stream_using_int(terms, term, scoretype, fh):
    for year in sorted(terms[term][scoretype].keys()):
        score = terms[term][scoretype][year]
        score = 'None' if score is None else "%d" % score
        fh.write("%s\t" % score)
    fh.write("%s\n" % term)

def print_from_stream(stream, outfile, scores_p):
    if scores_p:
        fh = codecs.open(outfile, 'w', encoding='utf8')
        fh.write(stream.getvalue())


if __name__ == '__main__':

    tscores_p = False
    mscores_p = False
    fscores_p = False
    kscores_p = False
    options = ['technology', 'frequency', 'maturity', 'keyterms', 'all']
    (opts, args) = getopt.getopt(sys.argv[1:], '', options)
    for opt, val in opts:
        if opt == '--technology': tscores_p = True
        if opt == '--maturity': mscores_p = True
        if opt == '--frequency': fscores_p = True
        if opt == '--keyterms': kscores_p = True
        if opt == '--all':
            tscores_p = True
            mscores_p = True
            fscores_p = True
            kscores_p = True

    terms = initialize_terms(mscores_p, fscores_p, kscores_p)
    add_tscores(terms)
    remove_non_technologies(terms)

    if mscores_p:
        add_mscores(terms)
    if fscores_p:
        add_fscores(terms)
        add_ascores(terms)
    if kscores_p:
        add_kscores(terms)

    print_terms(terms, tscores_p, mscores_p, fscores_p, kscores_p)
