# script to run term_features.sh with set parameters
# this populates the directory $TARGET/data/term_features/ with a subdirectory for each year
# specified, creating one file for each d3_phr_feats file in the source corpus.  Each 
# file contains a term, a feature, and the count of appearances of the feature with the term.
# The option ta/tas indicates which source file sections to use (title, abstract, summary)

#sh run_term_features.sh

# Peter's cs_2002_subset of 100 patents
#sh term_verb.sh /home/j/anick/patent-classifier/ontology/creation/data/patents/cs_2002_subset/config/files.txt /home/j/anick/patent-classifier/ontology/creation/data/patents/cs_2002_subset/data/d3_phr_feats/01/files /home/j/anick/patent-classifier/ontology/creation/data/patents/cs_2002_subset/data/m1_term_verb tas

# Marc cs 284k files from 1980 to 2007
#sh term_verb.sh /home/j/marc/Desktop/fuse/code/patent-classifier/ontology/creation/data/patents/201306-computer-science/config/files.txt /home/j/marc/Desktop/fuse/code/patent-classifier/ontology/creation/data/patents/201306-computer-science/data/d3_phr_feats/01/files /home/j/anick/patent-classifier/ontology/creation/data/patents/cs_284k/data/m1_term_verb tas

# This uses a larger set of cs files from BAE with application year in first column of files.txt file.  This will
# give more accurate time series information.
#sh term_verb.sh /home/j/corpuswork/fuse/FUSEData/corpora/ln-cs-500k/subcorpora/1995/config/files.txt /home/j/corpuswork/fuse/FUSEData/corpora/ln-cs-500k/subcorpora/1995/data/d3_phr_feats/01/files /home/j/anick/patent-classifier/ontology/creation/data/patents/cs_500k/data/m1_term_verb tas

# output in the form: <term> <verb> <count>
# influence       has     2

# setting this script up to loop over files from year 1995 - 2007.

#ROOT=/home/j/corpuswork/fuse/FUSEData/corpora/ln-us-all-600k
#TARGET=/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-all-600k

# Make sure target directory tree exists:
#bash-4.1$ mkdir ln-us-all-600k
#bash-4.1$ cd ln-us-all-600k
#bash-4.1$ mkdir data
#bash-4.1$ cd data
#bash-4.1$ mkdir term_features

# web of science
#ROOT="/home/j/corpuswork/fuse/FUSEData/corpora/wos-cs-520k"                                                       
#TARGET="/home/j/anick/patent-classifier/ontology/creation/data/patents/wos-cs-520k"                             
# cs patents (1997 - 2007)
ROOT="/home/j/corpuswork/fuse/FUSEData/corpora/ln-us-cs-500k"                                                       
TARGET="/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k"                             

# random us patent subset 600k
#ROOT="/home/j/corpuswork/fuse/FUSEData/corpora/ln-us-all-600k"
#TARGET="/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-all-600k"

# chinese general patents
#ROOT="/home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k"
#TARGET="/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-cn-all-600k"

# chemistry
#ROOT="/home/j/corpuswork/fuse/FUSEData/corpora/ln-us-12-chemical"                                                       
#TARGET="/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-12-chemical"                             

# health
#ROOT="/home/j/corpuswork/fuse/FUSEData/corpora/ln-us-14-health"
#TARGET="/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-14-health"

# Make sure target directory tree exists before running this script
mkdir $TARGET
mkdir $TARGET/data
mkdir $TARGET/data/term_features
mkdir $TARGET/data/tv

# loop over the years for which we have data
#"COMMENT"
#YEAR=1997
#YEAR=1998
YEAR=2003
#while [ $YEAR -le 1998 ] ; do
#while [ $YEAR -le 1997 ] ; do
while [ $YEAR -le 2007 ] ; do
    echo "year: $YEAR"

    sh term_features.sh $ROOT/subcorpora/$YEAR/config/files.txt $ROOT/subcorpora/$YEAR/data/d3_phr_feats/01/files $TARGET/data/term_features tas
    
    YEAR=$[ $YEAR + 1 ]
done
#COMMENT

