"""

Script to generate counts for positive and negative samples in the annotation files.

Usage:
    
    % python accumulate.py en/phr_occ.lab en/phr_occ.uct en/phr_occ.cum

"""


import sys, codecs

fh0 = codecs.open(sys.argv[1])
fh1 = codecs.open(sys.argv[2])
fh2 = codecs.open(sys.argv[3], 'w')

positives = {}
for line in fh0:
    if line.startswith('y'):
        term = line.strip().split("\t")[1]
        positives[term] = True
        
line_no = 0
total_count = 0
positives_count = 0
for line in fh1:
    line_no += 1
    count, term = line.strip().split("\t")
    if positives.has_key(term):
        positives_count += int(count)        
    total_count += int(count)
    fh2.write("%d\t%s\t%d\t%d\t%s\n" % (line_no, count, total_count, positives_count, term))
