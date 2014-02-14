"""create-master-list.py

Create a master file list for a corpus given a list of patent ids. 

Usage:

    $ python create-master-list.py PATENT_IDS MASTER_LIST WARNINGS

PATENT_IDS is a file with one patent identifier per line. MASTER_LIST is a file
with three columns: application date, publication date and full path to the
file. This is the file format used as the master-file.txt files in the fuse
composite corpora (ln-us-cs-500k etcetera). Warnings are written to WARNINGS if
we have no data for a particular patent (usually beause we could not extract the
needed dates).

For identifier lookup the script uses ln_uspto.all.index.sqlite in
/home/j/corpuswork/fuse/FUSEData/lists, an SQLite database of the full US index.

"""

import os, sys, sqlite3

PATENT_IDX = '/home/j/corpuswork/fuse/FUSEData/lists/ln_uspto.all.index.sqlite'

def get_base_dir(c):
    c.execute('SELECT * FROM base_dir')
    return c.fetchone()[0]

def get_patent_data(c, id):
    c.execute('SELECT * FROM data WHERE patent_id=?', (id,))
    return c.fetchone()


if __name__ == '__main__':

    fh_in = open(sys.argv[1])
    fh_out = open(sys.argv[2], 'w')
    fh_warnings = open(sys.argv[3], 'w')

    conn = sqlite3.connect(PATENT_IDX) 
    c = conn.cursor()
    base_dir = get_base_dir(c)

    count = 0
    fh_in.readline()  # skip the initial comment with full category name
    for line in fh_in:
        count += 1
        if count % 10000 == 0: print count
        id = line.strip()
        try:
            (appdate, pubdate, path) = get_patent_data(c, id)[1:4]
        except TypeError:
            fh_warnings.write("no data for %s\n" % id)
        path = os.path.join(base_dir, path)
        fh_out.write("%s\t%s\t%s\n" % (appdate, pubdate, path))
