"""

Simplify CNKI directory structure by removing spurious elements of the path.

It replaces paths like

   HY3/2007/E/ZHPF/ZHPF200708034/ZHPF200708034.fuse.xml

with

   HY3/2007/E/ZHPF/ZHPF200708034.fuse.xml

The result is more compact directories and reduced use of inodes.

Usage:

    python simplify-structure/py (d1d1|d1d2|hy2|hy3|d1|d2)

    The argument is a shorthand for one of the subpaths of the CNKI directory:

        Drive1/disk1
        Drive1/disk2
        HY2
        HY3
        disk1
        disk2

Progress and warnings are prinited to log files.

"""


import os, sys, shutil

CNKI_DIR = '/home/j/corpuswork/fuse/FUSEData/cnki'
LISTS_DIR = CNKI_DIR + '/information/tar-lists/targz-fuse-xml-all/vlist-grep'

EXT = 'fuse-xml-all-targz-vlist-grep.txt'
FILES = { 'd1d1': LISTS_DIR + '/CNKI-Drive1-disk1-' + EXT,
          'd1d2': LISTS_DIR + '/CNKI-Drive1-disk2-' + EXT,
          'hy2': LISTS_DIR + '/CNKI-HY2-' + EXT,
          'hy3': LISTS_DIR + '/CNKI-HY3-' + EXT,
          'd1': LISTS_DIR + '/CNKI-disk1-' + EXT,
          'd2': LISTS_DIR + '/CNKI-disk2-' + EXT }

def simplify(id, vlist_file):
    fh_progress = open("log-progress-%s.txt" % id, 'w')
    fh_warnings = open("log-warnings-%s.txt" % id, 'w')
    print vlist_file
    c = 0
    for line in open(vlist_file):
        c += 1
        if c % 1000 == 0:
            fh_progress.write("%d\n" % c)
            fh_progress.flush()
        #if c > 10: break
        path = line.split()[-1]
        long_dir = os.path.split(path)[0]
        short_dir = os.path.split(long_dir)[0]
        basename = os.path.basename(path)
        src = os.path.join(CNKI_DIR, long_dir, basename)
        dst = os.path.join(CNKI_DIR, short_dir, basename)
        if not os.path.exists(src):
            fh_warnings.write("File does not exist:%s\n" % src)
            fh_warnings.flush()
        elif not os.path.isdir(os.path.dirname(dst)):
            fh_warnings.write("Directory does not exist %s\n" % short_dir)
            fh_warnings.flush()
        else:
            shutil.move(src, dst)
            os.rmdir(os.path.dirname(src))
        
        
if __name__ == '__main__':

    id = sys.argv[1]
    simplify(id, FILES[id])
    #simplify('d2', FILES['d2'])
    
