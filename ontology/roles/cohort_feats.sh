# cohort_feats.sh

# for each year of a filtered cohort (cohort with specified growth conditions),  
# output the diagnostic features for each term in the cohort for each year
# also compute the relative year (feature year - cohort year)

# sh cohort_feats.sh ln-us-A21-computers 1998 1999
# sh cohort_feats.sh ln-us-A22-communications 1998 2005 hl

# get path info
source ./roles_config.sh

CORPUS=$1
# note that start year should be the year of the earliest cohort.<type> file
START_YEAR=$2
END_YEAR=$3
# FILTER_TYPE is hl or hh, as specified when creating cohorts using
# e.g., rfa22.filter_range(1998, 2007, 2, 5, 5, 10000, 0, 10, "hl") 
FILTER_TYPE=$4

ROOT="$LOCAL_CORPUS_ROOT/$CORPUS"

YEAR=$START_YEAR
# reset internal field separator to newline only (default is ' \t\n')
# so that each line is treated as a term, regardless of spaces
OIFS=$IFS
IFS=$'\n'

OUTPUT_FILE=$ROOT/data/tv/cohort2feats

while [ $YEAR -le $END_YEAR ] ; do

    COHORT_FILE=$ROOT/data/tv/$YEAR.cohort.$FILTER_TYPE
    # use tail -n +2 to skip the first line in the file
    COHORT_LINES="$(tail -n +2 $COHORT_FILE)"


    #echo "COHORT_LINES: $COHORT_LINES"

    for LINE in $COHORT_LINES; do
    	TERM=$(echo $LINE | cut -f1 )
        #echo "term: $TERM"
	FEAT_YEAR=$YEAR
    
	while [ $FEAT_YEAR -le $END_YEAR ] ; do
	    REL_YEAR=$[ 1 + ($FEAT_YEAR - $YEAR) ]
	    #echo "TERM: $TERM, COHORT: $YEAR, YEAR: $FEAT_YEAR, REL_YEAR: $REL_YEAR"
	    FEAT_FILE=$ROOT/data/tv/$FEAT_YEAR.tf.d20
	    #echo "FEAT_FILE: $FEAT_FILE"
	    GREP_RESULT=$(egrep "^$TERM	" $FEAT_FILE)
	    for GLINE in $GREP_RESULT ; do
		echo "$YEAR $REL_YEAR $GLINE"
		done
	    FEAT_YEAR=$[ $FEAT_YEAR + 1 ]
        done
    done

    echo "[create_tfd20] Completed corpus: $CORPUS, year: $YEAR"
    YEAR=$[ $YEAR + 1 ]

done
 

