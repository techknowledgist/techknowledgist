"""

Data utility to split the master list created with create-master-list.py.

Usage:
    python split-master-list.py
    
Creates a sereis of file in the cs-500K corpus on corpuswork:

    - a file with 51,000 t=random patents
    - files with all patents from particular years

The years are application years. A file for an application year has three
columns: year, path and shortpath. The short path contains the publication year
and the patent name. The year in the random file is not the application year but
th epublication year. May want to consider changing this.Also the random file is
random over the entire corpus, that is, for some years there are many more
instances.

"""

import random

# this is the master list created by create-master-list.py
MASTER_LIST = '/home/j/corpuswork/fuse/FUSEData/corpora/cs-500k/master-list.txt'

LISTS_DIR = '/home/j/corpuswork/fuse/FUSEData/corpora/cs-500k/sublists'


def get_pubdate_and_name(path):
        path_elements = path.split("/")
        pubyear = path_elements[-3]
        patent_name = path_elements[-1]
        return (pubyear, patent_name)

    
ALL_PATENTS = []

YEAR_INDEX = {}

for line in open(MASTER_LIST):
    (appdate, pubdate, source, path) = line.split()
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