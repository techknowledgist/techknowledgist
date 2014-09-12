# script to sort uniq .fc files for given years and root data
# This creates a unique count file based on the .fc data
# sh run_fc2fcuc.sh

# Chinese
#ROOT="/home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k"
#TARGET="/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-cn-all-600k"

# English computer science patents
#ROOT="/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv"
ROOT=$1
START_YEAR=$2
END_YEAR=$3
TARGET=$ROOT

# loop over the years for which we have data
#"COMMENT"
YEAR=$START_YEAR
while [ $YEAR -le $END_YEAR ] ; do
#while [ $YEAR -le 2007 ] ; do
    echo "[run_fc2fcuc.sh]year: $YEAR"

    sort $ROOT/$YEAR.fc | uniq -c | python reformat_uc2.py | sort > $ROOT/$YEAR.fc.uc

    YEAR=$[ $YEAR + 1 ]
done
#COMMENT

