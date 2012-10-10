#!/bin/sh
# 2012 08 29 PGA

# top level bash shell script for extracting useful sections from patent docs in multiple directories

# args:
# 1: patent_dir  -  a full path (without final slash) containing subdirectoris of
# lexis-nexis patents in xml format (one directory per year)
# 2: sent_dir  - a full path in corresponding subdirectories will be created, 
# in which selected sentences from each patent will
# be written.  If the directory or subdirectory does not exist, it will be created.  There should be
# one file created for each file in the patent_dir.

# e.g.
# sh sents_my.sh /home/j/clp/chinese/corpora/fuse-patents/500-patents/DATA/Lexis-Nexis/US/Xml /home/j/anick/fuse/data/patents/en
# sh sents_my.sh /home/j/clp/chinese/corpora/fuse-patents/500-patents/DATA/Lexis-Nexis/CN/Xml /home/j/anick/fuse/data/patents/CN
# sh sents_my.sh /home/j/clp/chinese/corpora/fuse-patents/500-patents/DATA/Lexis-Nexis/DE/Xml /home/j/anick/fuse/data/patents/DE

# Loop through the input directory, calling sents.sh for each subdirectory found
INPUT_DIRS=$1/*
OUTPUT_DIR=$2
for input_dir in $INPUT_DIRS
do
    echo $input_dir
    year=$(basename "$input_dir")
    echo $year

    output_subdir=$OUTPUT_DIR/sent/$year
    echo " => $output_subdir"

    # create the output dir if it does not exist
    if [ ! -d "$OUTPUT_DIR" ]; then
    # Control will enter here if $DIRECTORY doesn't exist.
	echo "[sents_my.sh]Creating dir: $OUTPUT_DIR"
	mkdir $OUTPUT_DIR
    fi

    # call sents.sh to create the subdir and sent files
    sh sents.sh $input_dir $output_subdir



done