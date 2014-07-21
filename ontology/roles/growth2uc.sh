# growth2uc.sh
# Use the growth files to generate unique count files for the cohort terms

# sh growth2uc.sh ln-us-cs-500k 1998 "b1 b2 b3 c1 c2 c3"
# sh growth2uc.sh ln-us-cs-500k 1998 "c3 c2 c1 b3 b2 b1

# After running, post-process to get out top terms in a given year as features
# cat 1998.growth.c3 | cut -f1,3 | sort | uniq -c | sort -nr | grep '2000    ' > 1998.growth.c3.2000.20"

CORPUS=$1

ROOT="/home/j/anick/patent-classifier/ontology/creation/data/patents"
DIR=$ROOT/$CORPUS/data/tv

Y1=$2
TYPES=$3


for TYPE in $TYPES; do
    GROWTH_FILE=$DIR/$Y1.growth.$TYPE
    GROWTH_LW_FILE=$DIR/$Y1.growth.lw.$TYPE
    UC_FILE=$GROWTH_FILE.uc
    UC_LW_FILE=$GROWTH_LW_FILE.uc

    # make sure the output files are empty to begin with
    > $UC_FILE=$GROWTH_FILE.uc
    > UC_LW_FILE=$GROWTH_LW_FILE.uc

    cat $GROWTH_FILE | cut -f2,3 | sort | uniq | cut -f2 | sort | uniq -c | python reformat_uc1.py | sort -nr > $UC_FILE
    cat $GROWTH_LW_FILE | cut -f2,4 | sort | uniq | cut -f2 | sort | uniq -c | python reformat_uc1.py | sort -nr > $UC_LW_FILE
    done
