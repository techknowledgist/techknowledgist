"""

Takes a corpus and concatenates all phr_feats files into a single file

Usage:

    $ python concatenate_features.py CORPUS OUTFILE

TODO: this script, and others, should probably live in another directory

"""


import os, sys, codecs, glob, gzip


corpus = sys.argv[1]
outfile = sys.argv[2]

fh_out = codecs.open(outfile, 'w', encoding='utf-8')

feats_dir = os.path.join(corpus, 'data', 'd3_phr_feats', '01', 'files')
regexp = "%s/WoS.out.*/*.xml.gz" % feats_dir
fnames = glob.glob(regexp)

count = 0
for fname in fnames:
    count += 1
    print "%05d %s" % (count, fname)
    gzipfile = gzip.open(fname, 'rb')
    reader = codecs.getreader('utf-8')
    fh = reader(gzipfile)
    for line in fh:
        fh_out.write(line)
