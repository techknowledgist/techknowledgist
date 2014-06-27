"""

Script for data list manipulation. Select the first 50,000 of the random list of
patents, but skip those that occur on the random sample of 500.

37 chalciope-> data/patents> python select-files.py
Skipping: /home/j/corpuswork/fuse/FUSEData/2013-04/ln_uspto/2008/074/US20080129292A1.xml
Skipping: /home/j/corpuswork/fuse/FUSEData/2013-04/ln_uspto/1990/004/US4964316A.xml
Skipping: /home/j/corpuswork/fuse/FUSEData/2013-04/ln_uspto/1980/013/US4219853A.xml
Skipping: /home/j/corpuswork/fuse/FUSEData/2013-04/ln_uspto/2004/019/US6759613B2.xml

"""


import os

ALL_FILES = "/home/j/corpuswork/fuse/FUSEData/lists/ln_uspto.all.shuffled.txt"
SAMPLE_500 = "sample-500-en-basic.txt"

RANDOM_50K = "random-50k-en-basic.txt"

sample_500 = {}
for line in open(SAMPLE_500):
    fname = os.path.basename(line.rstrip())[2:-4]
    sample_500[fname] = True

fh = open(RANDOM_50K, 'w')
count = 0
for line in open(ALL_FILES):
    fname, path = line.split()
    if not sample_500.has_key(fname):
        fh.write(path + "\n")
        count += 1
    else:
        print "Skipping:", path
    if count >= 50000:
        break
