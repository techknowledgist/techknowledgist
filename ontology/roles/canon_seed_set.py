# given a seed set of features that are not canonicalized, 
# output canonicalized seed set

#python2.7 canon_seed_set.py < seed.pn.en.dat > seed.pn.en.canon.dat
#python2.7 canon_seed_set.py < seed.act.en.dat > seed.act.en.canon.dat 
import canon
import sys

d_feat2label = {}

can = canon.Canon()

for line in sys.stdin:
    line = line.strip()
    (label, feature) = line.split("\t")
    d_feat2label[can.get_canon_feature(feature)] = label

l_out = []    
for key in d_feat2label.keys():
    l_out.append(d_feat2label[key] + "\t" + key)

for item in sorted(l_out):
    print "%s" % item


