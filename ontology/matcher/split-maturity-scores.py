
"""

Takes the tables in maturity-freq-based.txt and maturity-match-based.txt
and splits them into simpler tables for each year.

"""


import os, codecs

CORPUS_DIR = '/home/j/corpuswork/fuse/FUSEData/corpora/ln-us-cs-500k'
CORPUS_DIR = '/home/j/corpuswork/fuse/FUSEData/corpora/ln-us-all-600k'
#CORPUS_DIR = '/home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k'

TIME_SERIES_DIR = CORPUS_DIR + '/time-series-v2/maturity-scores'
#TIME_SERIES_DIR = CORPUS_DIR + '/time-series-v2/maturity-scores-cn'

maturity_scores1_file = TIME_SERIES_DIR + '/maturity-freq-based.txt'
maturity_scores2_file = TIME_SERIES_DIR + '/maturity-match-based.txt'


for filename in (maturity_scores1_file, maturity_scores2_file):

    print filename
    fh_in = codecs.open(filename)
    first_line = fh_in.readline()
    years = first_line.split()[:-1]

    fh_out = {}
    base, ext = os.path.splitext(filename)
    for year in years:
        outfile = base + '-' + year + ext
        print "Initializing", outfile
        fh_out[year] = codecs.open(outfile, 'w')

    lines = 0
    for line in fh_in:
        lines += 1
        #if lines > 100: break
        if lines % 100000 == 0: print lines
        fields = line.rstrip("\n\r").split("\t")
        term = fields[-1]
        i = -1
        #print line,
        #print fields
        for year in years:
            i += 1
            #print '  ', year, fields[i], term
            fh_out[year].write("%s\t%s\n" % (term, fields[i]))
