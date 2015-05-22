"""

Analyze the structure of CNKI.

Prints results to standard output.

Does not actualle parse the structure but uses the vlist-grep files in
information/tar-lists/targz-fuse-xml-all/vlist-grep.

A synopsis of the results:

    1- all filepaths have 9 elements for Drive1
    2- all filepaths have 8 elements for HY2
    3- all filepaths have 6 elements for HY3
    4- all filepaths have 8 elements for drive1 and drive2
    5- the last two are almost always the same (modulo the extension)
    6- the basenames are almost always unique

There is 1 exception to 5 and 6 in HY3:

Warning: non-unique basename ZHPF200708034.fuse.xml
   HY3/2007/E/ZHPF/ZHPF200708034/ZHPF200708034.fuse.xml
   HY3/2007/E/ZHPF/ZHPF200708034.PDF/ZHPF200708034.fuse.xml

The directory named HY3/2007/E/ZHPF/ZHPF200708034.PDF/ did show up in the result
and the files were identical so I deleted the ZHPF200708034.PDF version.

"""

import os, sys

CNKI_DIR = '/home/j/corpuswork/fuse/FUSEData/cnki'
LISTS_DIR = CNKI_DIR + '/information/tar-lists/targz-fuse-xml-all/vlist-grep'

EXT = 'fuse-xml-all-targz-vlist-grep.txt'
FILES = { 'd1d1': LISTS_DIR + '/CNKI-Drive1-disk1-' + EXT,
          'd1d2': LISTS_DIR + '/CNKI-Drive1-disk2-' + EXT,
          'hy2': LISTS_DIR + '/CNKI-HY2-' + EXT,
          'hy3': LISTS_DIR + '/CNKI-HY3-' + EXT,
          'd1': LISTS_DIR + '/CNKI-disk1-' + EXT,
          'd2': LISTS_DIR + '/CNKI-disk2-' + EXT }


def analyze_file(vlist_file):
    print os.path.basename(vlist_file)
    is_hy2 = vlist_file.find('-HY2') > -1
    is_hy3 = vlist_file.find('-HY3') > -1
    is_drive1 = vlist_file.find('-Drive1') > -1
    basenames = {}
    part_counts = {}
    last_two_equal = 0
    last_two_not_equal = 0
    aabb_all = {}
    for i in range(9):
        part_counts[i] = {}
    lengths = {}
    c = 0
    for line in open(vlist_file):
        c += 1
        if c % 100000 == 0:
            sys.stdout.write("%d " % c)
            sys.stdout.flush()
        #if c > 10000: break
        fname = line.split()[-1]
        #print fname
        parts = fname.split(os.sep)
        basename = parts[-1]
        if basenames.has_key(basename):
            print "\nWarning: non-unique basename", basename
            print '  ', fname
            print '  ', basenames[basename]
        basenames[basename] = fname
        length = len(parts)
        lengths[length] = lengths.get(length,0) + 1
        for i in range(length):
            part_counts[i][parts[i]] = True
        last_two = parts[-2:]
        if last_two[0] == last_two[1].replace('.fuse.xml', ''):
            last_two_equal += 1
        else:
            last_two_not_equal += 1
        if is_hy2:
            aabb = parts[4:6]
            aabb_all[''.join(aabb)] = True
        elif is_hy3:
            aabb = parts[3]
            aabb_all[aabb] = True
        elif is_drive1:
            aabb = parts[5:7]
            aabb_all[''.join(aabb)] = True
        else:
            aabb = parts[4:6]
            aabb_all[''.join(aabb)] = True

    print_results(lengths, part_counts, basenames, aabb_all,
                  last_two_equal, last_two_not_equal)

def print_results(lengths, part_counts, basenames, aabb_all,
                  last_two_equal, last_two_not_equal):
    print "\nlengths of paths:", lengths
    print_counts(part_counts)
    print "last two equal:", last_two_equal
    print "last two not equal:", last_two_not_equal
    print "unique AABB:", len(aabb_all)
    print
    
def print_counts(counts):
    print "unique parts per path position:"
    for i in sorted(counts):
        print '  ', i, len(counts[i])


if __name__ == '__main__':

    analyze_file(FILES['d1d1'])
    analyze_file(FILES['d1d2'])
    analyze_file(FILES['hy2'])
    analyze_file(FILES['hy3'])
    analyze_file(FILES['d1'])
    analyze_file(FILES['d2'])
