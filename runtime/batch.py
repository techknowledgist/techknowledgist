"""

Simple batch script for some testing.

"""

import os, sys, glob
from main import run


# Run the system in monolingual mode on the 38 patents from 2005. For each file we create
# a new Tagger instance. This takes a bit under 1 second per file, and would take about an
# hour for 5000 patents.

if 0:
    DIR = "/home/j/corpuswork/fuse/fuse-patents/500-patents/DATA/Lexis-Nexis/US/Xml/2005/"
    files = glob.glob("%s/*.xml" % DIR)
    for infile in files:
        basename = os.path.basename(infile)
        outfile = os.path.join('data', 'out', basename + ".tech")
        run('en', None, None, infile, outfile, 'MONO')

# Run it in batch on the same files so that you only have to create one Tagger instance.

if 1:
    DIR = "/home/j/corpuswork/fuse/fuse-patents/500-patents/DATA/Lexis-Nexis/US/Xml/2005/"
    files = glob.glob("%s/*.xml" % DIR)
    file_list = 'data/tmp/file_list.txt'
    fh = open(file_list, 'w')
    for infile in files:
        fh.write(infile+"\n")
    fh.close()
    run('en', 'data/out', file_list, None, None, 'MONO')
    
