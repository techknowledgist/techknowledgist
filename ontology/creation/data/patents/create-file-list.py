"""

Takes a file with file paths and creates two files each with three columns:
year, file path, short path. The short path just contains the year and the
filename.

The second file will have the files in random order.

Can be used as input to the -f option of step1_initialize.py.

Assumes that the path includes one subdir that encodes a year (that is, a
four-digit integer).

Usage:

    $ python create-file-list.py INFILE OUTFILE1 OUTFILE2


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
    parsed_path = long_path.split(os.sep)
    fname = parsed_path[-1]
    year = [p for p in parsed_path if len(p) == 4 and p.isdigit()][0]
    short_path = os.path.join(year, fname)
    saved_lines.append([year, long_path, short_path])

for (year, long_path, short_path) in saved_lines:
    fh_out1.write("%s\t%s\t%s\n" % (year, long_path, short_path))

random.shuffle(saved_lines)

for (year, long_path, short_path) in saved_lines:
    fh_out2.write("%s\t%s\t%s\n" % (year, long_path, short_path))
