"""

$ python compare_files.py en/technology/phr_occ.lab en/technology/phr_occ.20130218.relab out.lab

"""


import sys, codecs

base_file = sys.argv[1]
other_file = sys.argv[2]
out_file = sys.argv[3]

base_fh = codecs.open(base_file, encoding='utf-8')
other_fh = codecs.open(other_file, encoding='utf-8')
out_fh = codecs.open(out_file, 'w', encoding='utf-8')


the_others = {}

for line in other_fh:
    (label, term) = line.strip().split("\t")
    #print label, term
    the_others[term] = label

for line in base_fh:
    (label, term) = line.rstrip().split("\t")
    other_label = the_others.get(term,'')
    out_fh.write("%s\t%s\t%s\n" % (label, other_label, term))
