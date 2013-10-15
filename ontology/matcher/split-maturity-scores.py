
import os, codecs

CORPUS_DIR = '/home/j/corpuswork/fuse/FUSEData/corpora/cs-500k'
TIME_SERIES_DIR = CORPUS_DIR + '/time-series/maturity-scores'

maturity_scores1_file = TIME_SERIES_DIR + '/maturity-freq-based.txt'
maturity_scores2_file = TIME_SERIES_DIR + '/maturity-match-based.txt'


for filename in (maturity_scores1_file, maturity_scores2_file):

    fh_in = codecs.open(maturity_scores1_file)
    first_line = fh_in.readline()
    years = first_line.split()[:-1]

    fh_out = {}
    base, ext = os.path.splitext(filename)
    for year in years:
        outfile = base + '-' + year + ext
        print outfile
        fh_out[year] = codecs.open(outfile, 'w')

    for line in fh_in:
        fields = line.rstrip("\n\r").split("\t")
        term = fields[-1]
        i = -1
        for year in years:
            i += 1
            #print year, fields[i], term
            fh_out[year].write("%s\t%s\n" % (term, fields[i]))
