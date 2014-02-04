# script to create .uc files with set parameters
#sh run_term_uc.sh

# setting this script up to loop over files from year 1995 - 2007.

XML_DIR=/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_500k/data/m1_term_counts_tas
OUT_DIR=/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_500k/data/m2_mi_tas
CODE_DIR=/home/j/anick/patent-classifier/ontology/creation

# loop over the years for which we have data
#"COMMENT"
#YEAR=1996
YEAR=2000
while [ $YEAR -le 2007 ] ; do
#while [ $YEAR -le 1995 ] ; do
    echo "year: $YEAR"

    # This approach gives "argument list too long" error when the number of files in the dir exceed some threhold
    #cat $XML_DIR/$YEAR/*.xml | cut -f1 | sort | uniq -c | python $CODE_DIR/reformat_uc2.py > $OUT_DIR/$YEAR.uc

    # workaround also fails
    #ls -1  $XML_DIR/$YEAR/*.xml | while read file; do cat $file >> $OUT_DIR/$YEAR.all; done
    #cat $OUT_DIR/$YEAR.all | cut -f1 | sort | uniq -c | python $CODE_DIR/reformat_uc2.py > $OUT_DIR/$YEAR.uc 

    # workaround 2
    { echo $XML_DIR/$YEAR/*.xml | xargs cat; } > $OUT_DIR/$YEAR.all
    cat $OUT_DIR/$YEAR.all | cut -f1 | sort | uniq -c | python $CODE_DIR/reformat_uc2.py > $OUT_DIR/$YEAR.uc

    YEAR=$[ $YEAR + 1 ]
done
#COMMENT

