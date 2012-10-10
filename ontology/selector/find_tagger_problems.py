"""

Throw away script to compare titles in txt and tag files.

Usage:

    % python find_tagger_problems.py [LANGUAGE]

"""

import os, sys, glob, codecs
from config import BASE_DIR

LANG = 'de' if len(sys.argv) < 2 else sys.argv[1]
dir1 = os.path.join(BASE_DIR, LANG, 'txt')
dir2 = os.path.join(BASE_DIR, LANG, 'tag')

def find_title(fh, prefix):
    print_title = False
    for line in fh:
        if line.startswith('FH_TITLE'):
            print_title = True
        elif line.startswith('FH_'):
            print_title = False
        elif print_title:
            print '  ', prefix, '<', line[:80].strip(), '>'
            return

for year in sorted(glob.glob("%s/????" % (dir1))):
    print year
    date = os.path.basename(year)
    for fname1 in sorted(glob.glob("%s/*.xml" % (year))):
        fname2 = os.path.join(dir2, os.path.basename(year), os.path.basename(fname1))
        print date, os.path.basename(fname1)
        fh1 = codecs.open(fname1)
        fh2 = codecs.open(fname2)
        find_title(fh1, 'txt')
        find_title(fh2, 'tag')
