"""

Scans the source data directory with Web of Science data in WOS_DIR and selects
the computer science abstracts from all years in YEARS.

Usage:

    $ python read_cs_docs.py YEAR*

    Optionally, the years to process can be given as arguments, overriding the
    default setting of 1997 through 2007

Example:

    $ python read_cs_docs.py 2000 2001 2002

Input files to the WosReader are gzipped files like WoS.out.1998000001.gz. For
each of these, a new file like WoS.out.1998000001 is created in the cs-filtered
subdirectory, that file has all cs abstracts separated by white lines and
surrounded by wos-item tags. The tags are numbered, the numbers reflect the
abstract's position in the archive, measured in item offset.

A follow up script would takes these files and create individual files for each
abstract, grouped in directories for years.


TODO

This code worked fine up to and including 2003, but in later years it would hang
inexplicably. There were problems with:

    WoS.out.2004000031 WoS.out.2004000032 WoS.out.2004000036

    WoS.out.2005000005 WoS.out.2005000022 WoS.out.2005000030

    WoS.out.2006000013 WoS.out.2006000022 WoS.out.2006000023
    WoS.out.2006000024 WoS.out.2006000027 WoS.out.2006000029

    WoS.out.2007000005 WoS.out.2007000028 WoS.out.2007000029

For all these years, I stopped processing the corpus after the last file listed,
missing at least half the CS abstracts in those years.

"""


import os, sys, glob, codecs


from utils import WosReader

WOS_DIR = '/home/j/corpuswork/fuse/FUSEData/2013-04/WoS_2012_Aug/'
YEARS = [1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007]

# change this if you want to limit the number of files per year
# TODO: add back in the code to skip the first n files of a year
MAX_FILES_PER_YEAR = 3

# change if you want to only process some number of documents per file
MAX_DOCS_PER_FILE = 1000


if len(sys.argv) > 1:
    YEARS = [int(y) for y in sys.argv[1:]]

for year in YEARS:
    files = glob.glob("%s/WoS.out.%d*" % (WOS_DIR, year))
    files_done = 0
    for infile in files:
        files_done += 1
        if files_done > MAX_FILES_PER_YEAR: break
        all_documents = 0
        cs_documents = 0
        outfile = 'cs-filtered/' + os.path.basename(infile)[:-3]
        print "\n%s --> %s\n" % (infile, outfile)
        fh_out = codecs.open(outfile, 'w')
        reader = WosReader(infile)
        while True:
            wosdoc = reader.read()
            if wosdoc is None: break
            if all_documents >= MAX_DOCS_PER_FILE: break
            if all_documents % 100 == 0:
                print "  documents processed: %d" % all_documents
            all_documents += 1
            if wosdoc.is_cs_document() and wosdoc.is_okay():
                cs_documents += 1
                wosdoc.write_to_file(fh_out, id=all_documents)
        print "\nALL DOCUMENTS: %5d" % all_documents
        print "CS DOCUMENTS:  %5d" % cs_documents
