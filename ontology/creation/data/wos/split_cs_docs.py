"""

Takes all the documents generated with read_cs_docs.py and splits them into
individual documents.

"""


import os, glob, codecs, re

YEARS = range(1997, 2008)
year_exp = re.compile('^<bib_date .*year="(\d+)"')
LAST_FILE_ID = 0
FILE_LISTS = {}
STATS_SIZES = {}

def initialize_corpora():
    for year in YEARS:
        subcorpus = os.path.join('cs-corpora', str(year))
        if not os.path.exists(subcorpus):
            print "Creating", subcorpus
            os.mkdir(subcorpus)
        add_file_list(year, subcorpus)

def add_file_list(year, subcorpus):
    filelist = os.path.join(subcorpus, 'files.txt')
    FILE_LISTS[year] = open(filelist, 'w')
    
def ensure_path(path):
     if not os.path.exists(path):
        os.mkdir(path)

def next_id():
    global LAST_FILE_ID
    LAST_FILE_ID += 1
    return "%06d" % LAST_FILE_ID


def split_file(fname):
    fh = codecs.open(fname)
    text = fh.read()
    print fname, len(text),
    year = int(fname[20:24])
    wos_items = text.split("\n\n")
    c1 = 0
    c2 = 0
    total_items_size = 0
    for wos_item in wos_items[:-1]:  # skip the empty one at the end
        c1 += 1
        #if c > 4: break
        total_items_size += len(wos_item)
        item_year = year
        for line in wos_item.split("\n"):
            if line.startswith('<bib_date '):
                search_result = year_exp.search(line)
                if search_result is not None:
                    item_year = int(search_result.group(1))
                break
        wrote_item = write_wos_item(item_year, year, fname, wos_item)
        if wrote_item:
            c2 += 1
    print "%d %d/%d" % (total_items_size, c2, c1)


def write_wos_item(item_year, year, fname, text):
    dir = os.path.join('cs-corpora', str(item_year), os.path.basename(fname))
    file_id = next_id()
    if item_year in YEARS:
        ensure_path(dir)
        filename = os.path.join(dir, "%s.xml" % file_id)
        long_path = os.path.abspath(filename)
        short_path = filename[16:]
        FILE_LISTS[item_year].write("%d\t%s\t%s\n" % (item_year, long_path, short_path))
        with codecs.open(filename, 'w') as fh:
            fh.write(text + u"\n")
        return True
    return False


if __name__ == '__main__':

    initialize_corpora()
    fnames = sorted(glob.glob('cs-filtered/WoS*'))
    c = 0
    for fname in fnames:
        c += 1
        #if c > 5: break
        split_file(fname)



"""

156 chalciope-> wos/cs-corpora> du -ksh *
190M 1997
211M 1998
172M 1999
232M 2000
246M 2001
313M 2002
304M 2003
243M 2004
87M  2005
92M  2006
80M  2007

157 chalciope-> wos/cs-corpora> cd ../cs-filtered/
158 chalciope-> wos/cs-filtered> du -ksh
661M.


"""
