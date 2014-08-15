"""

Create scaffolding for domain corpora using the list with patents for 10 domains
as selected by MITRE.

Creates ten domains with names like:
    ln-uspto-A21-computers
    ln-uspto-A22-communications

In each there will be subdirectories named 'subcorpora' and 'sublists' where the
latter has the sublists that can be used for initialization of subcorpora.

"""


import os, sqlite3

FUSE_DATA = '/home/j/corpuswork/fuse/FUSEData'

# index of all patents <patent_id, app_date, pub_date, relative path>
PATENT_INDEX = FUSE_DATA + '/lists/ln_uspto.all.index.txt'
PATENT_INDEX = FUSE_DATA + '/lists/ln_uspto.all.index.sqlite'

# base path to add to the relative path
USPTO_BASE = FUSE_DATA + '/2013-04/ln_uspto'

# list with patents for the 10 MITRE categories
CATEGORIES = FUSE_DATA + '/lists/patentsByGtf.csv'

# short names adapted from lists/patentsByGtf.txt
CATEGORY_NAMES = {
    'A21': 'Computers',
    'A22': 'Communications',
    'A23': 'Semiconductors',
    'A24': 'Optical-Systems',
    'A25': 'Chemical-Engineering',
    'A26': 'Organic-Chemistry',
    'A27': 'Molecular-Biology',
    'A28': 'Mechanical-Engineering',
    'A29': 'Thermal-Technology',
    'A30': 'Electrical-Circuits' }

# index for filehandles for file lists in domains
FILE_LISTS = {
    'A21': {}, 'A22': {}, 'A23': {}, 'A24': {}, 'A25': {},
    'A26': {}, 'A27': {}, 'A28': {}, 'A29': {}, 'A30': {} }

# cursor into the index
CONNECTION = sqlite3.connect(PATENT_INDEX)
CURSOR = CONNECTION.cursor()


def initialize_domains():
    for id, name in CATEGORY_NAMES.items():
        domain =  "ln-us-%s-%s" % (id, name.lower())
        os.mkdir(domain)
        os.mkdir(os.path.join(domain, 'subcorpora'))
        os.mkdir(os.path.join(domain, 'sublists'))

def add_to_domain(patent_id, cat):
    CURSOR.execute('SELECT * FROM data WHERE patent_id=?', (patent_id,))
    result = CURSOR.fetchone()
    if result is not None:
        (patent, appdate, pubdate, path) = result
        appyear = appdate[:4]
        longpath = USPTO_BASE + '/' + path
        #print cat, appyear, patent, path
        add_to_filelist(cat, appyear, path, longpath)

def add_to_filelist(cat, appyear, path, longpath):
    #print cat, appyear, path, longpath
    if FILE_LISTS[cat].get(appyear) is None:
        filelist = "ln-us-%s-%s/sublists/%s.txt" % (cat, CATEGORY_NAMES[cat].lower(), appyear)
        #print "creating", filelist
        FILE_LISTS[cat][appyear] = open(filelist, 'w')
    FILE_LISTS[cat][appyear].write("%s\t%s\t%s\n" % (appyear, longpath, path))



        
if __name__ == '__main__':

    initialize_domains()
    count = 0
    for line in open(CATEGORIES):
        count +=  1
        if count % 1000 == 0: print count
        #if count > 2000: break
        try:
            (patent_id, year, category) = line.strip().split(',')
            (x, y, z, cat, v) = category.split('-')
            if cat.startswith('A'):
                add_to_domain(patent_id, cat)
        except ValueError:
            print line,
