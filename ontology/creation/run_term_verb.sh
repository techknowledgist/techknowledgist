# script to run term_verb.sh with set parameters
#sh run_term_verb.sh

# PGA : THIS IS REPLACED BY run_term_features.sh 

# Peter's cs_2002_subset of 100 patents
#sh term_verb.sh /home/j/anick/patent-classifier/ontology/creation/data/patents/cs_2002_subset/config/files.txt /home/j/anick/patent-classifier/ontology/creation/data/patents/cs_2002_subset/data/d3_phr_feats/01/files /home/j/anick/patent-classifier/ontology/creation/data/patents/cs_2002_subset/data/m1_term_verb tas

# Marc cs 284k files from 1980 to 2007
#sh term_verb.sh /home/j/marc/Desktop/fuse/code/patent-classifier/ontology/creation/data/patents/201306-computer-science/config/files.txt /home/j/marc/Desktop/fuse/code/patent-classifier/ontology/creation/data/patents/201306-computer-science/data/d3_phr_feats/01/files /home/j/anick/patent-classifier/ontology/creation/data/patents/cs_284k/data/m1_term_verb tas

# This uses a larger set of cs files from BAE with application year in first column of files.txt file.  This will
# give more accurate time series information.
#sh term_verb.sh /home/j/corpuswork/fuse/FUSEData/corpora/ln-cs-500k/subcorpora/1995/config/files.txt /home/j/corpuswork/fuse/FUSEData/corpora/ln-cs-500k/subcorpora/1995/data/d3_phr_feats/01/files /home/j/anick/patent-classifier/ontology/creation/data/patents/cs_500k/data/m1_term_verb tas

# Web of science (old feature set) 1997-2007
#
#CORPUS_ROOT="/home/j/corpuswork/fuse/FUSEData/corpora/wos-cs-520k"
#OUTPUT_ROOT="/home/j/anick/patent-classifier/ontology/creation/data/patents/wos-cs-520k_old"

# ln-cs-500 500k cs patents  
# CORPUS_ROOT="/home/j/corpuswork/fuse/FUSEData/corpora/ln-cs-500k"
# OUTPUT_ROOT="/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_500k"

# output in the form: <term> <verb> <count>
# influence       has     2

# setting this script up to loop over files from year 1995 - 2007.

# loop over the years for which we have data
#"COMMENT"
YEAR=1996
while [ $YEAR -le 2007 ] ; do
#while [ $YEAR -le 1995 ] ; do
    echo "year: $YEAR"

    sh term_verb.sh $OUTPUT_ROOT/subcorpora/$YEAR/config/files.txt $OUTPUT_ROOT/subcorpora/$YEAR/data/d3_phr_feats/01/files $OUTPUT_ROOT/data/m1_term_verb tas

    YEAR=$[ $YEAR + 1 ]
done
#COMMENT

