#!/bin/sh
# 2012 09 14 PGA

# top level bash shell script for using stanford dependency parser to 
# chunk pubmed formatted output (each line a sentence.

# args:
# 1: patent_dir  -  a full path (without final slash) containing
# lexis-nexis patents in xml format
# 2: sent_dir  - a full path in which selected sentences from each patent will
# be written.  If the directory does not exist, it will be created.  There should be
# one file created for each file in the patent_dir.
# 1: tag_dir  - a full path in which tagged sentences for each patent in sent_dir will
# be written.  If the directory does not exist, it will be created.  There should be
# one .tag file created for each file in the patent_dir.  Additionally, there will be one
# .over file created per input file.   These will be empty unless some sentence in the 
# input exceeds the length that can be handled by the Stanford parser.  Any such
# sentences will be output here.

# e.g.
# sh tags.sh /home/j/anick/fuse/data/patents/en/sent/1980 /home/j/anick/fuse/data/patents/en/tag/1980
# sh pubmed.sh > /home/j/anick/fuse/data/pubmed/chunks.txt

#sent_dir=$1
#tag_dir=$2

code_dir=/home/j/anick/fuse

#echo "Running code in dir: $code_dir"
cd $code_dir

python26 pubmed.py

#echo "Output written to $tag_dir"