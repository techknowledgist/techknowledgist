"""

Creates a file with usage information for terms in a corpus, using a set of
matches over the corpus and a classification over the corpus. WHat it basically
does is to combine information from the classifier output and the matcher output
for the usage/maturity patterns and prepare it for further processing down the
line (maturity scoring and time series).

Usage:

    $ python collect_usage_data.py OPTIONS

    --corpus DIRECTORY - the name/location of the corpus
    
    --matches DIRECTORY - the name of the matches directory inside the corpus,
      residing in the corpus directory in data/o2_matcher, the script picks out
      the file match.results.summ.txt in DIRECTORY
    
    --tscores DIRECTORY - a directory created by the technology classifier
      (ontology/classifier/tclassify.py), the script picks out the file
      classify.MaxEnt.out.s4.scores.sum.az
    
    --output FILE - output file to write the results to. 

    All options are required. For each option there is a short version (-c, -m,
    -t and -o).

The output is a file with for each term the technology score, the number of
documents the term occurs in and the number of matches for the term. The file
also has a header with information on how it was generated, input sources and a
few counts including total number of terms, total number of matches, highest
match count and highest document count. Terms are filtered, removing some
obvious crap. The total counts do not include the filtered terms or any data
relating to those filtered terms.

The terms are presented with three numbers as follows:

    1.0000   1   0   air sensor
    0.1136   1   0   air-handling unit
    0.1862   1   0   .31.5 example
    0.8852   1   0   adjoining plaques
    0.0003   1   1   ablation function

The first column has the average technology score for the term in the corpus,
the second the number of documents the term occurs in, and the third column the
number of matches for the term.


TODO

- add check that compares files.txt in the corpus and the files used for
  the classification
- add language parameter
- add CN term filter

"""



import os, sys, getopt, codecs

sys.path.append(os.path.abspath('../..'))
from ontology.utils.git import get_git_commit



def create_usage_file(corpus, matches, tscores, output):
    matches_file = os.path.join(corpus, 'data', 'o2_matcher', matches, 'match.results.summ.txt')
    tscores_file = os.path.join(tscores, 'classify.MaxEnt.out.s4.scores.sum.az')
    print "\nCreating usage statistics of terms\n"
    print "  corpus  =", corpus
    print "  matches =", os.path.basename(matches)
    print "  tscores =", os.path.basename(tscores)
    print "  output  =", output, "\n"
    term_matches = _read_matches(matches_file)
    usage_data = {}
    total_terms = 0
    total_matches = 0
    total_terms_with_matches = 0
    highest_match_count = 0
    highest_doc_count = 0
    c = 0
    print "Reading technology scores and document counts..."
    for line in codecs.open(tscores_file, encoding='utf-8'):
        c += 1
        if c % 100000 == 0: print '  ', c
        #if c > 200000: break
        term, score, doc_count, min, max = line.rstrip("\n\r\f").split("\t")
        if filter_term(term):
            continue
        total_terms += 1
        score = float(score)
        doc_count = int(doc_count)
        match_count = int(term_matches.get(term, 0))
        if match_count > 0:
                total_terms_with_matches += 1
        total_matches += match_count
        if match_count > highest_match_count:
            highest_match_count = match_count
        if doc_count > highest_doc_count:
            highest_doc_count = doc_count
        usage_data[term] = [score, doc_count, match_count]
    fh_out = codecs.open(output, 'w', encoding='utf-8')
    print "Writing usage data..."
    _write_info(fh_out, corpus, matches_file, tscores_file)
    _write_aggregate_counts(fh_out, total_terms, total_matches, total_terms_with_matches,
                            highest_match_count, highest_doc_count)
    _write_term_data(fh_out, usage_data)


def filter_term(term):
    return filter_term_en(term)

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

def _write_info(fh_out, corpus, matches, tscores):
    fh_out.write("\n$ python %s\n\n" % ' '.join(sys.argv))
    fh_out.write("git_commit = %s\n\n" % get_git_commit())
    fh_out.write("corpus  = %s\n" % corpus)
    fh_out.write("matches = %s\n" % matches)
    fh_out.write("tscores = %s\n" % tscores)
    fh_out.write("\n")

def _write_aggregate_counts(fh_out, total_terms, total_matches, total_terms_with_matches,
                            highest_match_count, highest_doc_count):
    fh_out.write("TOTAL_TERMS = %d\n" % total_terms)
    fh_out.write("TOTAL_MATCHES = %d\n" % total_matches)
    fh_out.write("TOTAL_TERMS_WITH_MATCHES = %d\n" % total_terms_with_matches)
    fh_out.write("HIGHEST_MATCH_COUNT = %d\n" % highest_match_count)
    fh_out.write("HIGHEST_DOC_COUNT = %d\n\n" % highest_doc_count)

def _write_term_data(fh_out, usage_data):
    for term in usage_data.keys():
        score, doc_count, match_count = usage_data[term]
        fh_out.write("%.4f\t%d\t%d\t%s\n" % (score, doc_count, match_count, term))

def _read_matches(match_file):
    """Return a hash for match_file, contains the number of matches for all
    terms from the file. The input file is assumed to have all scores for a
    particular year."""
    print "Reading term matches..."
    term_matches = {}
    for line in codecs.open(match_file):
        fields = line.split()
        matches = fields[0]
        term = ' '.join(fields[1:])
        term_matches[term] = matches
    return term_matches


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
    
    options = ['output=', 'corpus=', 'matches=', 'tscores=']
    (opts, args) = getopt.getopt(sys.argv[1:], 'o:c:m:t:', options)
    
    output = None
    corpus = None
    matches = None
    tscores = None
    
    for opt, val in opts:
        if opt in ('--output', '-o'): output = val
        elif opt in ('--corpus', '-c'): corpus = val
        elif opt in ('--matches', '-m'): matches = val
        elif opt in ('--tscores', '-t'): tscores = val

    check_args(corpus, matches, tscores, output)
    create_usage_file(corpus, matches, tscores, output)
