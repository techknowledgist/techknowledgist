"""

Takes the CNKI file with names and paths and create a file that can be input to
corpus creation, that is, a file with three columns: year, file path, short
path. The short path just contains the year and the filename.

The result can be used as input to the -f option of step1_initialize.py.

Assumes that the path includes one substring that encodes a year (that is, a
four-digit integer).

Usage:

    $ python create-file-list.py NUMBER_OF_LINES OUTFILE

    NUMBER_OF_LINES is an integer hat determines how many lines to take from the
    CNKI file list.


"""


import os, sys, re

YEAR_EXP = re.compile('/(\d\d\d\d)/')
CNKI_DIR = '/home/j/corpuswork/fuse/FUSEData/cnki'
CNKI_LIST = os.path.join(CNKI_DIR, 'cnki-all-random.txt')

def get_year(path):
    result = YEAR_EXP.search(path)
    if result is None:
        print "WARNING, no year in %s\n" % path
        return '9999'
    else:
        return result.group(1)


list_size = int(sys.argv[1])
fh_out = open(sys.argv[2], 'w')

c = 0
for line in open(CNKI_LIST):
    c += 1
    if c > list_size:
        break
    name, path = line.strip().split("\t")
    year = get_year(path)
    path = os.path.join(CNKI_DIR, path)
    # one way to do the short path is to just use the year
    short_path = os.path.join(year, os.path.basename(path))
    # but this is a better way for larger copora, the short path keeps the CNKI
    # structure but chops off the common path prefix from CNKI_DIR
    short_path = path[len(CNKI_DIR)+1:]
    fh_out.write("%s\t%s\t%s\n" % (year, path, short_path))
