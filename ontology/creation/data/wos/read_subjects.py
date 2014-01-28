"""

Usage:

    $ python read_cs_docs.py YEAR*

    Optionally, the years to process can be given as arguments, overriding the
    default setting of 1997 through 2007

Example:

    $ python read_cs_docs.py 2000 2001 2002

"""


import os, sys, glob, codecs, re


from utils import WosReader

WOS_DIR = '/home/j/corpuswork/fuse/FUSEData/2013-04/WoS_2012_Aug/'
YEARS = [1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007]

# change this if you want to limit the number of files per year
MAX_FILES_PER_YEAR = sys.maxint

# change if you want to only process some other number of documents per file
MAX_DOCS_PER_FILE = 100


if len(sys.argv) > 1:
    YEARS = [int(y) for y in sys.argv[1:]]


SUBJECT_EXP = re.compile(">(.*)</subject>")
SUBJECTS = {}
ALL_SUBJECTS = {}

for year in YEARS:

    SUBJECTS = {}
    fh_out = open("out-subjects-%s.txt" % year, 'w')
    files = glob.glob("%s/WoS.out.%d*" % (WOS_DIR, year))
    files_done = 0
    for infile in files:
        files_done += 1
        if files_done > MAX_FILES_PER_YEAR: break
        all_documents = 0
        print "%s" % (infile)
        reader = WosReader(infile)
        while True:
            wosdoc = reader.read()
            if wosdoc is None: break
            if all_documents >= MAX_DOCS_PER_FILE: break
            if all_documents % 100 == 0 and MAX_DOCS_PER_FILE > 100:
                print "  documents processed: %d" % all_documents
            all_documents += 1
            for subj in wosdoc.subjects:
                result = SUBJECT_EXP.search(subj)
                if result is not None:
                    topic = result.groups(0)[0]
                    topic = topic.replace('&amp;', '&')
                    SUBJECTS[topic] = SUBJECTS.get(topic,0) + 1
                    ALL_SUBJECTS[topic] = ALL_SUBJECTS.get(topic,0) + 1

    for s in sorted(SUBJECTS.keys()):
        fh_out.write("%5d   %s\n" % (SUBJECTS[s], s))
    fh_out.close()


fh_out = open("out-subjects-all.txt", 'w')
for s in sorted(ALL_SUBJECTS.keys()):
    fh_out.write("%5d   %s\n" % (ALL_SUBJECTS[s], s))
