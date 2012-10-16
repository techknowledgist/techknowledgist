"""

Create an index with frequency counts of terms for each year. In addition, creates a file
that holds the total byte count for all files in each years. This can be used for
normalization.

Given a base directory (imported from config.py), it creates the following files:

    <base_directory>/<language>/idx/index
    <base_directory>/<language>/idx/index.sizes.txt

Usage:

    % python index.py [-l LANGUAGE] [-c N] [-d PATH]

    -l LANG  --  specifies the language, default is 'en'
    -c N     --  maximum numbers of files to process per year, default is 1000
    -d PATH  --  base directory of the data
    
    The source directory is expected to have subdirectories for each year (1980..2011)
    and each of those contains files with tagged output with lines as follows:

        dem_ART Markt_NN derzeit_ADV erhaeltliche_ADJA

    Intermediate files and the INDEX_FILE are written to the target directory.
    
"""


import glob, os, sys, codecs, cProfile, pstats, getopt, shelve

from config import BASE_DIR
from utils import read_opts

MAX_FILES = 1000
LANGUAGE = 'en'

def usage():
    print "Usage:"
    print "% python index.py [-l LANGUAGE] [-c N] [-d PATH]"


def create_index(source_dir, target_dir, maxfiles):
    
    subdirs = glob.glob(os.path.join(source_dir, "*"))
    print "%s%sindex" % (target_dir, os.sep)
    INDEX = shelve.open("%s%sindex" % (target_dir, os.sep))
    SIZES = open("%s%sindex.sizes.txt" % (target_dir, os.sep), 'w')
    for subdir in subdirs:
        year = os.path.basename(subdir)
        print subdir
        collect_counts(subdir, target_dir, year, maxfiles, SIZES)
        fh = codecs.open("%s%s%s.tab" % (target_dir, os.sep, year))
        for l in fh:
            (np, count) = l.strip().split("\t")
            val = INDEX[np] if INDEX.has_key(np) else {}
            val[year] = int(count) 
            INDEX[np] = val
    INDEX.close()

    
def collect_counts(fname, target_dir, year, maxfiles, sizes_fh):

    YEAR_INDEX = {}
    FH = codecs.open("%s%s%s.tab" % (target_dir, os.sep, year), 'w')
    files = glob.glob(os.path.join(fname, "*.xml"))[:maxfiles]

    total_size = 0
    for f in files:
        total_size += os.path.getsize(f)
        now_reading = None
        for line in codecs.open(f):
            if line.startswith('FH_'):
                now_reading = line.strip()
            else:
                (id, year, np, sentence) = line.strip().split("\t")
                YEAR_INDEX.setdefault(np, 0)
                YEAR_INDEX[np] += 1
    
    sizes_fh.write("%s\t%d\n" % (year, total_size))
    for t in sorted(YEAR_INDEX.keys()):
        FH.write("%s\t%d\n" % (t, YEAR_INDEX[t]))



if __name__ == '__main__':

    language = LANGUAGE
    maxfiles = MAX_FILES
    base_dir = BASE_DIR
    
    (opts, args) = read_opts('l:c:d:', [], usage)
    for opt, val in opts:
        if opt == '-l': language = val
        if opt == '-c': maxfiles = int(val)
        if opt == '-d': base_dir = val
            
    source_dir = os.path.join(base_dir, language, 'phr_occ')
    target_dir = os.path.join(base_dir, language, 'idx')
    create_index(source_dir, target_dir, maxfiles)

    if 0:
        # TODO: this is wrong now, needs to be updated
        command = "create_index('%s', '%s')" % (dir, index_file)
        # cProfile.run(command, 'profile.txt')
        p = pstats.Stats('profile.txt')
        p.sort_stats('cumulative').print_stats(20)
