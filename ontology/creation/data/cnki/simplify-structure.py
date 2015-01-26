"""

Simplify CNKI directory structure by removing spurious elements of the path. For
example, this script replaces the first path below with the second:

   HY3/2007/E/ZHPF/ZHPF200708034/ZHPF200708034.fuse.xml
   HY3/2007/E/ZHPF/ZHPF200708034.fuse.xml

The result is more compact directories and reduced use of inodes. Progress and
warnings are printed to log files.


Usage:

    $ python simplify-structure/py (d1d1|d1d2|hy2|hy3|d1|d2) filter?

The argument is a shorthand for one of the subpaths of the CNKI directory:

    Drive1/disk1
    Drive1/disk2
    HY2
    HY3
    disk1
    disk2

Because of the size of hy2 and hy3 and the slowness of this script on the nsf
share, you can also use identifiers that point to 1MB fragments of hy2 and hy3:
hy2-a, hy2-b, hy2-c, hy2-d, hy2-e, hy2-f, hy2-g, hy3-a, hy3-b and hy3-c. These
sub lists were created with split-vlist-file.py.

If a filter is added, then the string given is required to be an element of the
file path being simplified. This was need for those case where we simplified a
directory and it threw warnings indicating that something went wrong with
unarchiving. When this was the case, it was always for a particular year. To fix
it, we (1) removed the year from the simplified directory, (2) unarchived the
year again, (3) moved the year to its position in the simplified directory, and
(4) simplified it again. This happend for hy3-1997 and d1d1-2010. For the
former, we needed to re simplify two files (hy3-a and hy3-b) because the 1997
files were in both those files:

    $ python simplify-structure.py hy3-a 1997 &
    $ python simplify-structure.py hy3-b 1997 &

"""

import os, sys, shutil

CNKI_DIR = '/home/j/corpuswork/fuse/FUSEData/cnki'
LISTS_DIR = CNKI_DIR + '/information/tar-lists/targz-fuse-xml-all/vlist-grep'

EXT = 'fuse-xml-all-targz-vlist-grep.txt'
FILES = { 'd1d1': LISTS_DIR + '/CNKI-Drive1-disk1-' + EXT,
          'd1d2': LISTS_DIR + '/CNKI-Drive1-disk2-' + EXT,
          'hy2': LISTS_DIR + '/CNKI-HY2-' + EXT,
          'hy2-a': "CNKI-HY2-a-fuse-xml-all-targz-vlist-grep.txt",
          'hy2-b': "CNKI-HY2-b-fuse-xml-all-targz-vlist-grep.txt",
          'hy2-c': "CNKI-HY2-c-fuse-xml-all-targz-vlist-grep.txt",
          'hy2-d': "CNKI-HY2-d-fuse-xml-all-targz-vlist-grep.txt",
          'hy2-e': "CNKI-HY2-e-fuse-xml-all-targz-vlist-grep.txt",
          'hy2-f': "CNKI-HY2-f-fuse-xml-all-targz-vlist-grep.txt",
          'hy2-g': "CNKI-HY2-g-fuse-xml-all-targz-vlist-grep.txt",
          'hy3': LISTS_DIR + '/CNKI-HY3-' + EXT,
          'hy3-a': "CNKI-HY3-a-fuse-xml-all-targz-vlist-grep.txt",
          'hy3-b': "CNKI-HY3-b-fuse-xml-all-targz-vlist-grep.txt",
          'hy3-c': "CNKI-HY3-c-fuse-xml-all-targz-vlist-grep.txt",
          'd1': LISTS_DIR + '/CNKI-disk1-' + EXT,
          'd2': LISTS_DIR + '/CNKI-disk2-' + EXT }

def simplify(id, vlist_file, filter):
    name = "%s-%s" % (id, filter) if filter else id
    fh_progress = open("log-progress-%s.txt" % name, 'w')
    fh_warnings = open("log-warnings-%s.txt" % name, 'w')
    print vlist_file
    c = 0
    for line in open(vlist_file):
        if filter and line.find('/'+filter+'/') < 0:
            continue
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
    filter = sys.argv[2] if len(sys.argv) > 2  else False
    simplify(id, FILES[id], filter)
