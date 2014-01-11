"""

Select 25 random files from the results of a processing stage from a corpus.

Usage:

    $ python select-random-files.py CORPUS STAGE

Writes results to a directory random/CORPUS-STAGE. All files are unzipped.

Example:
    
    $ python select-random-sample.py \
      /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/1999 d2_seg

"""

import os, sys, glob, random

corpus = sys.argv[1]
stage = sys.argv[2]

COUNT = 25

corpus_name = os.path.basename(corpus)
files_dir = os.path.join(corpus, 'data', stage, '01', 'files')
results_dir = os.path.join('random', "%s-%s" % (corpus_name, stage))

print "Selecting from", files_dir

file_list = glob.glob("%s/????/*" % files_dir)
random.shuffle(file_list)


print "Collected", len(file_list), 'files'
print "Writing to", results_dir

os.mkdir(results_dir)
for fname in file_list[:COUNT]:
    (year, basename) = fname.split(os.sep)[-2:]
    print '  ', year, basename
    #print "cp %s %s/%s-%s" % (fname, results_dir, year, basename)
    os.system("cp %s %s/%s-%s" % (fname, results_dir, year, basename))
os.system("gunzip %s/*.gz" % results_dir)
