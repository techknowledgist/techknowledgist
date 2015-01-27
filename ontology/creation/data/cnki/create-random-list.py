"""

Create a random index of CNKI file paths, indexed on the short name of the path
(the base name with '.fuse.xml' removed).

Takes as input the grepped vlists, but removes the spurious part of the path.

Creates cnki-all-random.txt and cnki-all-random.log. The first has two columns
(short name and path), the second has all the cases where there were duplicates
(there were 19,159 cases of this).

Needs at least 5GB free memory to run.

"""


import os, sys, random

CNKI_DIR = '/home/j/corpuswork/fuse/FUSEData/cnki'
LISTS_DIR = CNKI_DIR + '/information/tar-lists/targz-fuse-xml-all/vlist-grep'

OUT_FILE = 'cnki-all-random.txt'
WARNINGS = 'cnki-all-random.log'

FH_WARNINGS = open(WARNINGS, 'w')

INDEX = {}

for fname in os.listdir(LISTS_DIR):
    print fname
    fpath = os.path.join(LISTS_DIR, fname)
    c = 0
    warnings = 0
    for line in open(fpath):
        c += 1
        if c % 100000 == 0: print '  ', c
        if c > 100: break
        # get the path and the base, but loose the suprious part of the path
        path = line.split()[-1]
        dir, basename = os.path.split(path)
        dir, rest = os.path.split(dir)
        path = os.path.join(dir, basename)
        basename = basename.replace('.fuse.xml', '')
        if INDEX.has_key(basename):
            warnings += 1
            FH_WARNINGS.write("duplicate entry for %s\n" % basename)
            FH_WARNINGS.write("   %s\n" % INDEX[basename][0])
            FH_WARNINGS.write("   %s\n" % path)
            INDEX[basename].append(path)
        else:
            INDEX[basename] = [path]
    print "   warnings:", warnings 
    
print "Getting all keys..."
cnki_fnames = INDEX.keys()
print "Done, got %d keys" % len(cnki_fnames)

print "Shuffling..."
random.shuffle(cnki_fnames)
print "Done."

print "Writing random file"
fh = open(OUT_FILE, 'w')
c = 0
for name in cnki_fnames:
    c += 1
    if c % 100000 == 0: print '  ', c
    for path in INDEX[name]:
        fh.write("%s\t%s\n" % (name, path))
print "Done"
