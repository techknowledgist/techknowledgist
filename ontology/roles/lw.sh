# lw.sh (last word analysis)

# growth file: /home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv/growth.c
# sh lw.sh ln-us-cs-500k c 100 > /home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv/growth.c.100.lw
# sh lw.sh ln-us-cs-500k c 3 > /home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv/growth.c.3.lw

# process the output:
# cat growth.c.3.lw | cut -f2,4 | sort | uniq | cut -f2 | sort | uniq -c | sortnr -k1 > growth.c.3.lw.uc
# cat growth.c.100.lw | cut -f2,4 | sort | uniq | cut -f2 | sort | uniq -c | sortnr -k1 > growth.c.100.lw.uc
# cat growth.c.100.lw | cut -f2,4 | sort | uniq -c | sortnr -k1 > growth.c.100.lw.uc
# This tells us which features have the broadest use across the set of high growth terms.  For the set of years,
# how many different terms appeared with this feature?

CORPUS=$1

ROOT="/home/j/anick/patent-classifier/ontology/creation/data/patents"
DIR=$ROOT/$CORPUS/data/tv
# cat is c,t, or a
CAT=$2
TERM_COUNT=$3

GROWTH_FILE=$DIR/growth.$CAT


# get list of terms from file in arg 1
#TERMS="$(< $1)"
#GROWTH_FILE_SUBSET="$(< $GROWTH_FILE)"

#echo "term count: $TERM_COUNT"
GROWTH_FILE_SUBSET="$(head -$TERM_COUNT $GROWTH_FILE)"

YEARS='1997 1998 1999 2000 2001 2002 2003 2004 2005 2006'
#YEARS='2005 2006'

# reset internal field separator to newline only (default is ' \t\n')
# so that each line is treated as a term, regardless of spaces
OIFS=$IFS
IFS=$'\n'

for LINE in $GROWTH_FILE_SUBSET; do
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
	GREP_RESULT=$(egrep "^$TERM " $DIR/$YEAR.tf | grep last_word | cut -f1,2,3)
	IFS=$'\n'
	for RESULT in $GREP_RESULT; do
	    echo "$YEAR	$TERM	$RESULT"
        done
    done
done
