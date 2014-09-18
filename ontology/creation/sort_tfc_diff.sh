# script to sort tfc.diff files for a range of years

#sh sort_tfc_diff.sh 7   (sort by adjusted change ratio)
#sh sort_tfc_diff.sh 8   (sort by raw freq difference)

# setting this script up to loop over files from year 1995 - 2007.

# col is the sort column
COL=$1
TFC_DIR=/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_500k/data/m2_tv
CODE_DIR=/home/j/anick/patent-classifier/ontology/creation

# loop over the years for which we have data
#"COMMENT"

# Year for .tfc.diff files is 1 greater than our earliest year file, since it
# is labeled by the later of the 2 years that are compared.
YEAR=1996
while [ $YEAR -le 2007 ] ; do
#while [ $YEAR -le 1996 ] ; do
    echo "year: $YEAR"

    # k7 is the adjusted change metric
    # k8 is raw freq difference
    cat $TFC_DIR/$YEAR.tfc.diff | sort -k$COL -nr -t'	' > $TFC_DIR/$YEAR.tfc.diff.k$COL

    YEAR=$[ $YEAR + 1 ]
done
#COMMENT

