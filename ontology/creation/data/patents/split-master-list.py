"""

Data utility to split the master list for a corpus, typically created with
create-master-list.py. or create_date_idx.py.

Usage:
    python split-master-list.py

Creates a series of file in the corpus directory indentified by CORPUS_DIR.

    - a file with 51,000 random patents
    - files with all patents from particular years

The years are application years. A file for an application year has three
columns: year, path and shortpath. The short path contains the publication year
and the patent name. The year in the random file is not the application year but
the publication year. May want to consider changing this. Also, the random file
is random over the entire corpus, that is, for some years there are many more
instances.

"""

import random

# Location of the master list and the directory of sublists. The master list is
# created by create-cs-master-list.py, create_date_idx.py (which was used when
# we still did not have the full date index) or create-master-list.py.

CORPUS_DIR = '/home/j/corpuswork/fuse/FUSEData/corpora/ln-us-all-600k'
CORPUS_DIR = '/home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k'
CORPUS_DIR = '/home/j/corpuswork/fuse/FUSEData/corpora/ln-us-12-chemical'
CORPUS_DIR = '/home/j/corpuswork/fuse/FUSEData/corpora/ln-us-14-health'

MASTER_LIST = CORPUS_DIR + '/master-list-14.txt'
LISTS_DIR = CORPUS_DIR + '/sublists'


def get_pubdate_and_name(path):
        path_elements = path.split("/")
        pubyear = path_elements[-3]
        patent_name = path_elements[-1]
        return (pubyear, patent_name)

    
ALL_PATENTS = []

YEAR_INDEX = {}

for line in open(MASTER_LIST):
    fields = line.split()
    if len(fields) == 4:
        # the master list for cs, created by create-master-list.py, has an extra
        # field with the source of the element in the list
        (appdate, pubdate, source, path) = fields
    else:
        (appdate, pubdate, path) = fields
    ALL_PATENTS.append(path)
    year = appdate[:4]
    YEAR_INDEX.setdefault(year,[]).append(path)

random.shuffle(ALL_PATENTS)
fh = open("%s/random-50k.txt" % LISTS_DIR, 'w')
count = 0
for path in ALL_PATENTS:
    count += 1
    (pubyear, patent_name) = get_pubdate_and_name(path)
    fh.write("%s\t%s\t%s/%s\n" % (pubyear, path, pubyear, patent_name))
    if count == 51000:
        break
fh.close()

for year in sorted(YEAR_INDEX.keys()):
    fh = open("%s/%s.txt" % (LISTS_DIR, year), 'w')
    print year, len(YEAR_INDEX[year])
    for path in YEAR_INDEX[year]:
        (pubyear, patent_name) = get_pubdate_and_name(path)
        fh.write("%s\t%s\t%s/%s\n" % (year, path, pubyear, patent_name))
    fh.close()
