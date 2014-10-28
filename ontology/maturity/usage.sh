
CORPORA=/home/j/corpuswork/fuse/FUSEData/corpora/ln-us-all-600k/subcorpora
CORPUS=$CORPORA/subcorpora/2000
CLASSIFICATION=$CORPORA/classifications/technologies-ds1000-all-2000
OUTPUT=usage.txt

python usage.py -c $CORPUS -m maturity -t $CLASSIFICATION -o $OUTPUT

more $OUTPUT
