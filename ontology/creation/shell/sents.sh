#!/bin/sh
# 2012 08 29 PGA

# top level bash shell script for extracting useful sections from patent docs.

# args:
# 1: patent_dir  -  a full path (without final slash) containing
# lexis-nexis patents in xml format
# 2: sent_dir  - a full path in which selected sentences from each patent will
# be written.  If the directory does not exist, it will be created.  There should be
# one file created for each file in the patent_dir.

# e.g.
# sh sents.sh /home/j/clp/chinese/corpora/fuse-patents/500-patents/DATA/Lexis-Nexis/US/Xml/1980 /home/j/anick/fuse/data/patents/en/sent/1980
# sh sents.sh /home/j/clp/chinese/corpora/fuse-patents/500-patents/DATA/Lexis-Nexis/CN/Xml/1987 /home/j/anick/fuse/data/patents/CN/sent/1987
# sh sents.sh /home/j/clp/chinese/corpora/fuse-patents/500-patents/DATA/Lexis-Nexis/DE/Xml/1982 /home/j/anick/fuse/data/patents/DE/sent/1982

patent_dir=$1
sent_dir=$2

code_dir=/home/j/anick/fuse

echo "Running code in dir: $code_dir"
cd $code_dir

python26 sents.py $patent_dir $sent_dir

echo "Output written to $sent_dir"