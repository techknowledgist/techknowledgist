# keyterm detection
# This file should be merged into patent_analyzer.py
# 7/10/13 PGA added parameter for an annotation subdirectory to 
# capture annotations for specific subsets (eg. cs_2002)

# To run:
# python key.py <annot_subdir> <patents_subdir>
# python key.py cs_2002 cs_2002_subset

# Before running this, make sure you have created a patents_subdir (under data/patents)
# and have placed a list of files to be used for training in $patents_subdir/config/key_train_files.txt
# train_file_list="/home/j/anick/patent-classifier/ontology/creation/data/patents/$patents_subdir/config/key_train_files.txt"

import config
import subprocess
import sys

target_path = config.WORKING_PATENT_PATH
language = config.LANGUAGE
annot_path = config.ANNOTATION_DIRECTORY + "/" + language + "/" + "invention"
annot_subdir = annot_path + "/" + sys.argv[1]
patents_subdir = sys.argv[2]

print "annot_subdir is: %s" % annot_subdir


command = "sh ./key.sh %s %s %s %s" % (target_path, annot_subdir, language, patents_subdir)
subprocess.call(command, shell=True)
