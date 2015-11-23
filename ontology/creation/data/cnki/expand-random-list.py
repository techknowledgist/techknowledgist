"""

Script that checks the random list of CNKI documents. The input is hardwired to
the cnki-all-random.txt list in CNKI_DIR.

Usage:

    $ python expand-random-list.py (SKIP LIMIT)?

    The optional arguments will cause the script to skip the first SKIP lines
    and to stop after line LIMIT. The defaults are 0 and 10.
    
For each document, it checks whether it exists, what the size it is, and from
what year it is (as taken from the file path). Results are written to two files:

    cnki-all-random-idx-LIMIT.txt
    cnki-all-random-idx-LIMIT.idx

The first has columns for the file name, the year, the size and the path. The
second writes log messages on progress, non-existing files, large files and file
with no year in the path. Each line in the log starts with a string indicating
what is reported.

This would take 14 days for all CNKI documents (based on a test that took 76
seconds for 1000 CNKI documents) so it needs to run in parallel on segments of
the input file. This is not yet supported by the code.

"""

import os, sys, re, time

CNKI_DIR = '/home/j/corpuswork/fuse/FUSEData/cnki'
RANDOM_LIST = os.path.join(CNKI_DIR, 'cnki-all-random.txt')

YEAR_EXP = re.compile('/(\d\d\d\d)/')


def process_list(skip=0, limit=10):
    c = 0
    for line in open(RANDOM_LIST):
        c += 1
        if c % 1000 == 0:
            LOG.write("PROGRESS\t%s\t%s\n" % (time.strftime("%x %X"), c))
            LOG.flush()
        if c <= skip: continue
        if c > limit: break
        name, path = line.split()
        year = get_year(path)
        cnki_fname = os.path.join(CNKI_DIR, path)
        try:
            size = os.path.getsize(cnki_fname)
            OUT.write("%s\t%s\t%s\t%s\n" % (name, year, size, path))
            if size > 100000:
                LOG.write("LARGE_FILE\t%d\t%s\n" % (size, path))
        except OSError:
            LOG.write("DOES_NOT_EXIST\t%s\n" % path)
            size = -1

def get_year(path):
    result = YEAR_EXP.search(path)
    if result is None:
        LOG.write("NO_YEAR\t%s\n" % path)
        return '9999'
    else:
        return result.group(1)


if __name__ == '__main__':

    if len(sys.argv) > 2:
        skip = int(sys.argv[1])
        limit = int(sys.argv[2])
    elif len(sys.argv) > 1:
        skip = 0
        limit = int(sys.argv[1])
    else:
        skip = 0
        limit = 10
    OUT = open("cnki-all-random-idx-%07d.txt" % limit, 'w')
    LOG = open("cnki-all-random-idx-%07d.log" % limit, 'w')
    t1 = time.time()
    process_list(skip, limit)
    print "Time elapsed: %d seconds" % (time.time() - t1)
