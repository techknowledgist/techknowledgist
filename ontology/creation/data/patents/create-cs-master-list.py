"""

Utility to create a master list of all CS patents.

Usage:
    % python create-cs-master-list.py

This results in three files, all starting with cs-master-list. One file has the
results, two two others contain a dribble and error me=ssages. The results file
has four fields for each patent:

    application_date
    publication_date
    source
    path

The source is one of [both, bae, nyu] and reflects whether the patent was
regarded a CS patnet by the BAE and/or NYU procedure to extract the CS patents.

Three files are needed as input:
    /home/j/corpuswork/fuse/FUSEData/lists/csPatents-path.txt
    /home/j/corpuswork/fuse/FUSEData/lists/computer_science.lteq2007.xml.pathlist.txt'
    /home/j/marc/Desktop/fuse/code/patent-classifier/utils/date_idx.txt

The first two are the paths of the CS patents as extracted by BAE and NYU
respectively. The third is an index with previous results of running the date
extraction code on the NYU patents.

"""


import os, re, random


LISTS_DIR = '/home/j/corpuswork/fuse/FUSEData/lists'
BAE_FILE = LISTS_DIR + os.sep + 'csPatents-path.txt'
NYU_FILE = LISTS_DIR + os.sep + 'computer_science.lteq2007.xml.pathlist.txt'
DATE_IDX_NYU = '/home/j/marc/Desktop/fuse/code/patent-classifier/utils/date_idx.txt'


def read_lists(bae_file, nyu_file, date_idx):

    patents = {}
    dates = {}

    print "reading", bae_file
    for line in open(bae_file):
        id, path = line.split()
        patents[path] = 'bae'

    print "reading", nyu_file
    for line in open(nyu_file):
        path = line.strip()
        if patents.has_key(path):
            patents[path] = 'both'
        else:
            patents[path] = 'nyu'

    print "reading", date_idx
    for line in open(date_idx):
        appdate, pubdate, path = line.split()
        dates[path] = (appdate, pubdate)

    patent_list = patents.items()
    print "sorting..."
    patent_list.sort()

    return patents, patent_list, dates


def find_dates(patents, dates):
    fh_results = open("cs-master-list.txt", 'w')
    fh_warnings = open("cs-master-list.err", 'w')
    fh_dribble = open("cs-master-list.dribble", 'w')
    count = 0
    for (path, source) in patents:
        if dates.has_key(path):
            appdate, pubdate = dates[path]
            fh_results.write("%s\t%s\t%s\t%s\n" % (appdate, pubdate, source, path))
            continue
        find_dates_using_grep(path, source, fh_results, fh_warnings)
        count += 1
        if (count % 100 == 0):
            fh_dribble.write("%d\n" % count)
            fh_results.flush()
            fh_warnings.flush()
            fh_dribble.flush()
            print count
        #if (count % 300 == 0): exit()


def find_dates_using_grep(fname, source, fh_results, fh_warnings):
    """Originally taken from utils/create_date_idxs.py."""
    appdate = None
    pubdate = None
    in_appref = False
    in_pubref = False
    lines_read = 0
    for line in open(fname):
        lines_read += 1
        text = line.strip()
        if text.startswith('<application-reference'):
            in_appref = True
            in_pubref = False
        if text.startswith('<publication-reference'):
            in_appref = False
            in_pubref = True
        if text.startswith('<date>'):
            if in_appref: appdate = text[6:14]
            if in_pubref: pubdate = text[6:14]
        if appdate and pubdate:
            fh_results.write("%s\t%s\t%s\t%s\n" % (appdate, pubdate, source, fname))
            return
    if not appdate and pubdate:
        fh_warnings.write("WARNING: funny stuff in %s\n" % fname)
    

def print_info(list):
    print
    print 'LENGTH ALL:', len(list)
    print 'LENGTH BOTH:', len(sublist(list, 'both'))
    print 'LENGTH BAE:', len(sublist(list, 'bae'))
    print 'LENGTH NYU:', len(sublist(list, 'nyu'))
    print "\nFIRST 10:"
    for p, s in list[:10]: print "   %-4s  %s" % (s, p)

def shuffle(list):
    random.shuffle(list)

def sublist(list, source):
    return [x for x in list if x[1] == source]
    

if __name__ == '__main__':

    patent_idx, patent_list, dates = read_lists(BAE_FILE, NYU_FILE, DATE_IDX_NYU)
    print_info(patent_list)
    find_dates(patent_list, dates)
    

