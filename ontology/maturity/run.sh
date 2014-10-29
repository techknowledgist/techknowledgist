
# example on how to run the script to collect usage data

CORPORA=/home/j/corpuswork/fuse/FUSEData/corpora/ln-us-all-600k
CORPUS=$CORPORA/subcorpora/2000
CLASSIFICATION=$CORPORA/classifications/technologies-ds1000-all-2000
OUTPUT=out.txt

python collect_usage_data.py -c $CORPUS -m maturity -t $CLASSIFICATION -o $OUTPUT
