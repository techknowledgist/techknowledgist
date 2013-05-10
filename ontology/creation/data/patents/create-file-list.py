"""

Takes a file with file paths and creates two files each with three columns: year, file
path, short path. The second file will have the files in random order.

Can be used as input to the -f option of step1_initialize.py.

The input for this could be created with

$ find /Users/marc/Documents/fuse/data/fuse-patents/500-patents/DATA/Lexis-Nexis/US/Xml -type f > ~/Documents/fuse/code/patent-classifier/ontology/creation/data/patents/sample-500-basic.txt

"""

import os, sys, random

fh_in = open(sys.argv[1])
fh_out1 = open(sys.argv[2], 'w')
fh_out2 = open(sys.argv[3], 'w')

saved_lines = []

for line in fh_in:
    long_path = line.strip()
    d1, fname = os.path.split(long_path)
    d2, year = os.path.split(d1)
    short_path = os.path.join(year, fname)
    saved_lines.append([year, long_path, short_path])

for (year, long_path, short_path) in saved_lines:
    fh_out1.write("%s\t%s\t%s\n" % (year, long_path, short_path))

random.shuffle(saved_lines)

for (year, long_path, short_path) in saved_lines:
    fh_out2.write("%s\t%s\t%s\n" % (year, long_path, short_path))
