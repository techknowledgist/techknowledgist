import os, glob, codecs

from config import BASE_DIR

dir = os.path.join(BASE_DIR, 'en', 'phr_feats')

print "%s%s*" % (dir, os.sep)

defined_fields = (
    'initial_V', 'lead_J', 'next_n3', 'next_n2', 'section', 'of_head', 'prev_n3',
    'prev_n2', 'last_word', 'initial_J', 'following_prep', 'prev_N', 'prev_V', 'tag_sig',
    'next_2tags')


def add_fields(fh, term, fields):
    result = []
    for f in defined_fields:
        v = fields.get(f, 'None')
        if v.find(',') > -1 or v.find('\'') > -1 :
            return
        result.append(v)
    result.append('yes') if term in positives else result.append('no')
    fh.write("%s\n" % ','.join(result))

positives = {}
negatives = {}
fh = codecs.open('annotations/en/phr_occ.lab')
for line in fh:
    (b, term) = line.rstrip().split("\t")
    if b == 'y':
        positives[term] = True
    if b == 'n':
        negatives[term] = True
#print positives

        
FIELDS = {}
fh_out = codecs.open('weka.arff', 'w')
fh_out.write("@relation technology\n\n")
for f in defined_fields:
    fh_out.write("@attribute %s string\n" % f)
fh_out.write("@attribute technology {yes, no}\n\n")
fh_out.write("@data\n")
    
for year in glob.glob("%s%s????" % (dir, os.sep)):
    print year
    for fname in glob.glob("%s/*.xml" % (year)):
        fh = codecs.open(fname)
        for line in fh:
            collected_fields = {}
            fields = line.strip().split("\t")
            term = fields[2]
            #print term
            if term in positives or term in negatives:
                feats = fields[4:]
                for feat in feats:
                    split_feat = feat.split('=')
                    if len(split_feat) == 2:
                        f, v = split_feat
                        FIELDS.setdefault(f, 0)
                        FIELDS[f] += 1
                        collected_fields[f] = v
                add_fields(fh_out, term, collected_fields)
    break

