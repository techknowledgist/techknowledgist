"""

Script to select a number of random patents from a master list.

Usage:

   $ python create-random-list.py

   There are no arguments, paameters can be changed by editing the global
   variables at the beginning of the script.

The input master list has three columns: (1) application date, (2) publication
date and (3) full source path, for example:

   19830621
   19860318
   /home/j/corpuswork/fuse/FUSEData/2013-04/ln_uspto/1986/004/US4577022A.xml

(There is an optional fourth column, which would be inserted before the path,
which has an indication of the source of line; this was used for the cs corpus,
where nyu and bae had different ways of defining what patents were in cs).

The output file is like the other output files, with three columns: (1) the
application year, (2) the full source path and (3) a short path that includes
just the application year, for example:

   2000
   /home/j/corpuswork/fuse/FUSEData/2013-04/ln_uspto/2001/001/US6263263B1.xml
   2000/US6263263B1.xml

Note that the output file does not have the publication year, except that the
full source path still refelcts this year.

"""

import os, random


# THE FOLLOWING CAN BE EDITED BY THE USER

# the input master list
MASTER_LIST = '../../../../utils/date_idx_0000000-0500000.txt'

# the output file
OUTFILE = 'random-50k.txt'

# the list with the 500 sample patents, from which the evaluation set is selected.
SAMPLE_500 = 'sample-500-basic.txt'

# total number of patents to add to the random set
TOTAL = 50000

# set to True if the input needs to be shuffled
SHUFFLE = False

# allowed range of years for the selected patents
FIRST_YEAR = 1997
LAST_YEAR = 2007

# NO EDITS NEEDED AFTER THIS


def get_pubdate_and_name(path):
        path_elements = path.split("/")
        pubyear = path_elements[-3]
        patent_name = path_elements[-1]
        return (pubyear, patent_name)

def read_master_list():
    patent_list = []
    count = 0
    for line in open(MASTER_LIST):
        count += 1
        if count > 100000: break
        fields = line.split()
        if len(fields) == 4:
            # the master list for cs, created by create-master-list.py, has an extra
            # field with the source of the element in the list
            (appdate, pubdate, source, path) = fields
        else:
            (appdate, pubdate, path) = fields
        year = appdate[:4]
        (pubyear, patent_name) = get_pubdate_and_name(path)
        patent_list.append([path, year, pubyear, patent_name])
    print "Read", MASTER_LIST
    return patent_list

def read_sample_500():
    sample_500 = {}
    for line in open(SAMPLE_500):
        sample_500[os.path.basename(line.strip())] = True
    print "Read %d patents from %s" % (len(sample_500), SAMPLE_500)
    return sample_500
    
def write_random_file(patents):
    fh = open(OUTFILE, 'w')
    count = 0
    for path, year, pubyear, patent_name in patents:
        if int(year) < FIRST_YEAR: continue
        if int(year) > LAST_YEAR: continue
        count += 1
        fh.write("%s\t%s\t%s/%s\n" % (year, path, year, patent_name))
        if count >= TOTAL:
            break
    fh.close()
    print "Wrote", OUTFILE


if __name__ == '__main__':
    
    patents = read_master_list()
    sample_500 = read_sample_500()
    if SHUFFLE:
        random.shuffle(patents)
        print "Shuffled patent list"
    write_random_file(patents)

