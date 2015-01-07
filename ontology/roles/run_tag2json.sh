# run_tag2json.sh
# script to run tag2json.sh with set parameters
# this populates the directory $TARGET/data/tv/ with a file for each year
# specified, creating one file for each d3_phr_feats file in the source corpus.  Each 
# file contains a term, a feature, and the count of appearances of the feature with the term.
# The option ta/tas indicates which source file sections to use (title, abstract, summary)

# NOT FINISHED!

# uses tf.py and term_features.sh

# example calls
# modified to take three parameters corpus, start_year, end_year
# sh run_term_features.sh wos-cs-520k 1997 1997
# sh run_term_features.sh ln-us-all-600k 1997 2007

# sh run_term_features.sh ln-us-A30-electrical-circuits 2002 2002
# 
# sh run_term_features.sh ln-us-A27-molecular-biology 1997 2007
# sh run_term_features.sh ln-us-A22-communications 1997 2007
# sh run_term_features.sh ln-us-A30-electrical-circuits 1998 2007

# PARAMETERS TO SET BEFORE RUNNING SCRIPT:
# FUSE_CORPUS_ROOT="/home/j/corpuswork/fuse/FUSEData/corpora"
# LOCAL_CORPUS_ROOT="/home/j/anick/patent-classifier/ontology/creation/data/patents"
# LOCAL_CORPUS_ROOT="/home/j/anick/patent-classifier/ontology/roles/data/patents"
# get the corpus roots from roles.config.sh

# 10/2/14 PGA removed the creation of the tf.f file, which is redundant with the .terms file information.

# sh run_tag2json.sh ln-us-A21-computers 2002 2003

# get start time to compute elapsed time
START_TIME=$(date +%s)

# get path info
source ./roles_config.sh

CORPUS=$1
START_YEAR=$2
END_YEAR=$3

#ROOT="/home/j/corpuswork/fuse/FUSEData/corpora/$CORPUS"
FUSE_ROOT=$FUSE_CORPUS_ROOT/$CORPUS
#TARGET="/home/j/anick/patent-classifier/ontology/creation/data/patents/$CORPUS"
LOCAL_ROOT="$LOCAL_CORPUS_ROOT/$CORPUS"

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

# These variables out of date.  Corpus now passed in as parameter.
# web of science
#ROOT="/home/j/corpuswork/fuse/FUSEData/corpora/wos-cs-520k"                                                       
#TARGET="/home/j/anick/patent-classifier/ontology/creation/data/patents/wos-cs-520k"                             
# cs patents (1997 - 2007)
#ROOT="/home/j/corpuswork/fuse/FUSEData/corpora/ln-us-cs-500k"                                                       
#TARGET="/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k"                             

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

echo "[run_term_features.sh]LOCAT_ROOT: $LOCAL_ROOT, LOCAL_CORPUS_ROOT: $LOCAL_CORPUS_ROOT" 

mkdir $LOCAL_ROOT
mkdir $LOCAL_ROOT/data
mkdir $LOCAL_ROOT/data/term_features
mkdir $LOCAL_ROOT/data/tv
# create a directory for ACT specific files
mkdir $LOCAL_ROOT/data/act

# we use final "/" for the parameters to run_dir2features_count
TF_DIR=$LOCAL_ROOT/data/term_features/
TV_DIR=$LOCAL_ROOT/data/tv

echo "[run_term_features.sh]Created local_root directory: $LOCAL_ROOT"

#exit 
# loop over the years for which we have data

YEAR=$START_YEAR
#YEAR=1998
#YEAR=2003
#while [ $YEAR -le 1998 ] ; do
# populate the local term_features directory for the range of years specified

#<<"COMMENT"
echo "[run_tag2json.sh]Populating tv directory for each year in range"
#exit

while [ $YEAR -le $END_YEAR ] ; do

    OUTFILE=$TV_DIR/$YEAR.json

    echo "[run_tag2json]year: [$YEAR], outfile: $OUTFILE"
    # create (or re-initialize to empty) the yearly outfile
    ###> $OUTFILE

    sh tag2json.sh $FUSE_ROOT/subcorpora/$YEAR/config/files.txt $FUSE_ROOT/subcorpora/$YEAR/data/d2_tag/01/files $OUTFILE tas
    
    YEAR=$[ $YEAR + 1 ]
done

