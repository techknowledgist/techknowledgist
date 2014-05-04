# make_tf_f.sh
# file is needed for input to phran.py

# uses <year>.tf to create <year>.tf.f
# which gives # docs containing the term for that year
# sh make_tf_f.sh ln-us-cs-500k

CORPUS=$1

ROOT="/home/j/anick/patent-classifier/ontology/creation/data/patents"
DIR=$ROOT/$CORPUS/data/tv
TF_QUAL="tf"
TFF_QUAL="tf.f"

YEARS='1997 1998 1999 2000 2001 2002 2003 2004 2005 2006'
#YEARS='1997'

for YEAR in $YEARS; do
    TF_FILE=$DIR/$YEAR.$TF_QUAL
    TFF_FILE=$DIR/$YEAR.$TFF_QUAL
    # clear the output file in case it already exists
    > $TFF_FILE
    #GREP_RESULT=$(grep "last_word" $TF_FILE | cut -f1,3)
    grep "last_word" $TF_FILE | cut -f1,3 >> $TFF_FILE
    
done
