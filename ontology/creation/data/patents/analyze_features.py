"""

Generate statistics on feature counts and their values. For each feature in the
input, a statistics file is written to the features directory.

The input file is expected to be a concatenation of all phr_feats file in a
corpus, possibly created by the classifier or by concatenate_features.py.

Usage:

    $ python analyze_features.py FILE_PATH?

    The optional argument is the file to be read, the default is
    features/201309-en.phr.tab

"""


import os, sys, codecs

FEATS_FILE = "features/201309-en.phr.tab"

if len(sys.argv) > 1:
    FEATS_FILE = sys.argv[1]


features = {}

count = 0
for line in codecs.open(FEATS_FILE):
    count += 1
    if count % 50000 == 0: print count
    #if count > 50000: break
    fields = line.strip().split("\t")
    for feat_val in  fields[3:]:
        feat, val = feat_val.split('=',1)
        if feat.endswith('loc'):
            continue
        features.setdefault(feat, {})
        features[feat][val] = features[feat].get(val,0) + 1

print features.keys()
for feat, dict in features.items():
    print 'printing', feat
    dirname = "features/%s" % FEATS_FILE
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    fh = codecs.open("%s/features-%s.txt" % (dirname, feat), 'w')
    fh.write("Total occurrences of %s in %s: %d\n\n" % 
             (feat, FEATS_FILE, sum(dict.values())))
    for w in sorted(dict, key=dict.get, reverse=True):
        if dict[w] > 5:
            fh.write("%d\t%s\n" % (dict[w], w))

      
exit()


# somehow the following does not work on the files as we have them

import os, sys, glob

sys.path.append(os.path.abspath('../../..'))

from utils.file import open_input_file

filenames = glob.glob("201309-en/data/d3_phr_feats/01/files/*/*")

features = {}

for fname in filenames:
    print fname
    fh = open_input_file(fname)
    print fh
    for line in fh:
        print line
        break
