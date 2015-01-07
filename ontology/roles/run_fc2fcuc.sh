# script to sort uniq .fc files for given years and root data
# This creates a unique count file based on the .fc data
# sh run_fc2fcuc.sh 

# Chinese
#ROOT="/home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k"
#TARGET="/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-cn-all-600k"

# English computer science patents
#ROOT="/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv"

TV_PATH=/data/tv

CORPUS_ROOT=$1
CORPUS=$2
START_YEAR=$3
END_YEAR=$4
CAT_TYPE=$5
SUBSET=$6

#echo "1. SUBSET is [$SUBSET]"

# SUBSET may be empty.  If not, we need to prepend a dot in order
# for the correct filepath to be created below
# to test for empty string, put argument in quotes and use -n operator
if [ -n "$SUBSET" ]
then SUBSET=".$SUBSET."
else SUBSET="."
fi 



# We cannot add the year to the filepath string since it gets set in a loop later
# But we can construct the pieces around it.
FILESTR_BEFORE_YEAR="$CORPUS_ROOT/$CORPUS$TV_PATH/"
FILESTR_AFTER_YEAR=$SUBSET$CAT_TYPE

echo "[run_fc2fcuc.sh] SUBSET is [$SUBSET], cat_type is [$CAT_TYPE], filestr_before_year is [$FILESTR_BEFORE_YEAR], filestr_after_year is [$FILESTR_AFTER_YEAR]"

# loop over the years for which we have data
#"COMMENT"
YEAR=$START_YEAR
while [ $YEAR -le $END_YEAR ] ; do
#while [ $YEAR -le 2007 ] ; do
    FILE_PREFIX=$FILESTR_BEFORE_YEAR$YEAR$FILESTR_AFTER_YEAR
    INPUTPATH=$FILE_PREFIX.fc
    OUTPUTPATH=$FILE_PREFIX.fc_uc

    echo "[run_fc2fcuc.sh]input_file: $INPUTPATH, output_file: $OUTPUTPATH "

    sort $INPUTPATH | uniq -c | python reformat_uc2.py | sort > $OUTPUTPATH

    YEAR=$[ $YEAR + 1 ]
done
#COMMENT

