"""
Script that takes a file list from the config directory (typically files.txt)
and then creates files with selections of training files and testing files.

Usage:

    python split-file-list FILELIST TRAINING_BASE TESTING_BASE TRAINING_SIZE TESTING_SIZE

    FILELIST       -  list with all the files in the corpus, with three columns
    TRAINING_BASE  -  basename for training file, .txt will be added
    TESTING_BASE   -  basename for testing files, _N.txt will be added
    TRAINING_SIZE  -  number of files to add to the training file
    TESTING_SIZE   -  number of files to add to each testing file

The first TRAINING_SIZE elements from FILELIST are added to TRAINING_BASE.txt
and testing files are numbered (TESTING_BASE_01.txt, TESTING_BASE_02.txt, ...),
each test file has TESTING_SIZE lines, except the last one, which can have less.
"""

import sys

infile, train_file, test_file,training_files, testing_files = sys.argv[1:6]
training_files, testing_files = int(training_files), int(testing_files)
test_file_count = 0
train_fh = open(train_file + '.txt', 'w')
test_fh = None

count = 0
for line in open(infile):
    if count % testing_files == 0:
        test_file_count += 1
        if test_fh is not None:
            test_fh.close()
        test_fh = open(test_file + "_%02d.txt" % test_file_count, 'w')
    year, longpath, shortpath = line.strip().split("\t")
    if count < training_files:
        train_fh.write(shortpath + "\n")
    test_fh.write(shortpath + "\n")
    count += 1
