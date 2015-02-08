"""

This script is a hack that fixes the usage scores and the number of matches in
the usage files.

Usage:

    $ python fix_usage_scores.py YYYY

This takes the usage file usage-YYYY.txt and match.results.summ.txt in the
subcorpora/YYYYdata/o2_matches/maturity subdirectory of the Chinese corpus at
/home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k and creates a file
usage-fixed-YYYY.txt.

Note. This is to work around a bug in collect_usage_scores.py that shows up with
Chinese data. I have not found the fix yet, but something seems to go wrong when
terms with Chinese charaters are stored in the hash.

Update. This script is now obsolete since collect_usage_scores.py was fixed.

"""


import sys, codecs, math

CORPUS = '/home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k'
MATURITY_SUBPATH = 'data/o2_matcher/maturity'


def read_matcher_results(matches_file):
    print "Reading", matches_file
    term_matches = {}
    for line in codecs.open(matches_file, encoding='utf-8'):
        fields = line.split()
        matches = fields[0]
        term = ' '.join(fields[1:])
        term_matches[term] = matches
    print 'Number of terms with matches', len(term_matches)
    return term_matches

def read_usage_scores(usage_file):
    print 'Reading', usage_file
    header = u''
    usage = {}
    c = 0
    for line in codecs.open(usage_file, encoding='utf-8'):
        c += 1
        #if c > 10000: break
        if c % 100000 == 0: print "%dk" % (c/1000,),
        if line.startswith('#'):
            header += line
        else:
            tscore, uscore, count, matches, term = line.rstrip("\n\r\f").split("\t")
            usage[term] = [tscore, uscore, count, matches]
    print
    return header, usage


if __name__ == '__main__':

    year = sys.argv[1]

    matches_file = "%s/subcorpora/%s/%s/match.results.summ.txt" % (CORPUS, year, MATURITY_SUBPATH)
    usage_file = "usage-%s.txt" % year
    fixed_usage_file =  "usage-fixed-%s.txt" % year

    header, usage = read_usage_scores(usage_file)
    matches = read_matcher_results(matches_file)

    print 'Updating matches'
    highest_matches = 0
    for term, matches in matches.items():
        if int(matches) > highest_matches:
            highest_matches = int(matches)
        if usage.has_key(term):
            usage[term][3] = matches

    # This code is similar to calculate_usage_rates() in collect_usage_scores.py
    print 'Updating usage scores'
    adjustment = math.log(highest_matches + 1.0001)
    for term in usage:
        [tscore, uscore, doc_count, match_count] = usage[term]
        uscore = math.log(int(match_count) + 1) / adjustment
        usage[term] = [tscore, uscore, doc_count, match_count]

    print 'Printing', fixed_usage_file
    fh = codecs.open(fixed_usage_file, 'w', encoding='utf8')
    fh.write(header)
    fh.write("# In addition, the usage score and matches count were fixed by\n")
    fh.write("#\n")
    fh.write("# $ python %s\n" % ' '.join(sys.argv))
    fh.write("#\n")
    for term in sorted(usage.keys()):
        (tscore, uscore, count, matches) = usage[term]
        fh.write("%s\t%.4f\t%s\t%s\t%s\n" % (tscore, uscore, count, matches, term))
    print
