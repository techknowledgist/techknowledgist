# cohort2growth.sh
# creates a growth file for a subset of the terms (of a specified type) in a cohort file
# NOTE: the range of years is currently hard coded.  This should be generalized to support any range and
# to start with the y1 year (to save time).

# input: <year>.cohort
# c3      network appliance       24      58
# output: <year>.growth.<type>
# 1999    google  last_word=google        10
# 1999    google  prev_Jpr=such_as        2
# 2000    google  last_word=google        22
#  2000    google  prev_Jpr=such_as        8
# 2001    google  prev_VNP=improve|aspect|of      1

# sh cohort2growth.sh ln-us-cs-500k 1998 b3 100
# sh cohort2growth.sh ln-us-cs-500k 1998 b2 100
# sh cohort2growth.sh ln-us-cs-500k 1998 c3 100
# sh cohort2growth.sh ln-us-cs-500k 1998 c2 100
# sh cohort2growth.sh ln-us-cs-500k 1998 b1 100
# sh cohort2growth.sh ln-us-cs-500k 1998 c1 100
# sh cohort2growth.sh ln-us-cs-500k 1998 b3 3 => /home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv/1998.growth.b3

# growth file: /home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv/growth
# sh occ.sh ln-us-cs-500k c 100 > /home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv/growth.c.100
# sh occ.sh ln-us-cs-500k c 3 > /home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv/growth.c.3

# process the output (growth and growth.lw)
# cat 1998.growth.b3 | cut -f2,3 | sort | uniq | cut -f2 | sort | uniq -c | sortnr -k1 > 1998.growth.b3.uc
# cat 1998.growth.lw.b3 | cut -f2,4 | sort | uniq | cut -f2 | sort | uniq -c | sortnr -k1 > 1998.growth.lw.b3.uc
# This tells us which features have the broadest use across the set of high growth terms.  For the set of years,
# how many different terms appeared with this feature?
# cat 1998.growth.b3 | cut -f2 | sort | uniq | wc -l    
# Above is # terms in this cohort

CORPUS=$1

ROOT="/home/j/anick/patent-classifier/ontology/creation/data/patents"
DIR=$ROOT/$CORPUS/data/tv
# Y1 (year 1) is the first year the term appears
Y1=$2
# type is one of a1,a2,a3,b1,b2,b3,c1,c2,c3 indicating growth pattern
TYPE=$3
# number of terms to output
TERM_COUNT=$4

COHORT_FILE=$DIR/$Y1.cohort

# get list of terms from file in arg 1
#TERMS="$(< $1)"
#COHORT_FILE_SUBSET="$(< $COHORT_FILE)"

#echo "term count: $TERM_COUNT"
COHORT_FILE_SUBSET=$(grep "^$TYPE" $COHORT_FILE | head -$TERM_COUNT | cut -f2,4 )\n 

#echo "COHORT_FILE_SUBSET: $COHORT_FILE_SUBSET"
#exit

YEARS='1997 1998 1999 2000 2001 2002 2003 2004 2005 2006'
#YEARS='2005 2006'

# reset internal field separator to newline only (default is ' \t\n')
# so that each line is treated as a term, regardless of spaces
OIFS=$IFS
IFS=$'\n'

GROWTH_FILE=$DIR/$Y1.growth.$TYPE
GROWTH_LW_FILE=$DIR/$Y1.growth.lw.$TYPE

# make sure output file is empty before appending lines
# (using builtin redirect (> file)
> $GROWTH_FILE
> $GROWTH_LW_FILE

for LINE in $COHORT_FILE_SUBSET; do
    #echo "line: $LINE"
    # use parameter expansion to get the term (chars before the tab)
    #echo "stripped line: ${LINE%	*}"
    TERM=${LINE%	*}
    #echo "term: $TERM"
    # restore the field separators to parse the year line (which uses whitespace separators)
    IFS=$OIFS
    for YEAR in $YEARS; do
	# use cntrl-q tab to input a tab in emacs
	#echo "$YEAR	$TERM"
	# for each year, grep the term
	#echo "tf file: $DIR/$YEAR.tf"
	#GREP_CMD="egrep '^$TERM	' $DIR/$YEAR.tf"
	#echo "grep cmd: $GREP_CMD"
	GREP_RESULT=$(egrep "^$TERM	" $DIR/$YEAR.tf | cut -f1,2,3)
	#echo "grep_result: $GREP_RESULT"
	IFS=$'\n'
	for RESULT in $GREP_RESULT; do
	    #echo "$YEAR	$RESULT"
	    echo -e "$YEAR	$RESULT" >> $GROWTH_FILE
	    done
    done

    # Now do the same for the last_word feature
    IFS=$OIFS

    for YEAR in $YEARS; do
	# use cntrl-q tab to input a tab in emacs
	#echo "$YEAR	$TERM"
	# for each year, grep the term
	#echo "tf file: $DIR/$YEAR.tf"
	#GREP_CMD="egrep '^$TERM	' $DIR/$YEAR.tf"
	#echo "grep cmd: $GREP_CMD"
	GREP_RESULT=$(egrep "^$TERM " $DIR/$YEAR.tf | grep last_word | cut -f1,2,3)
	IFS=$'\n'
	for RESULT in $GREP_RESULT; do
	    echo -e "$YEAR	$TERM	$RESULT" >> $GROWTH_LW_FILE
        done
    done
done
