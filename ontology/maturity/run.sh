
# example on how to run the script to collect usage data
# uses -l to stop after 200k lines in the terms file

if [ 1 = 0 ]; then
CORPORA=/home/j/corpuswork/fuse/FUSEData/corpora/ln-us-all-600k
CORPUS=$CORPORA/subcorpora/2000
CLASSIFICATION=$CORPORA/classifications/technologies-ds1000-all-2000
OUTPUT=out2.txt
python collect_usage_data.py -c $CORPUS -m maturity -t $CLASSIFICATION -o $OUTPUT --limit 200000
fi


# same, but on a set of corpora

if [ 1 = 1 ]; then
for year in 1997;# 1998 1999;# 2000 2001 2002 2003 2004 2004 2006 2007 2008 2009 2010 2011;
do
    CORPORA=/home/j/corpuswork/fuse/FUSEData/corpora/ln-us-all-600k
    CORPUS=$CORPORA/subcorpora/$year
    CLASSIFICATION=$CORPORA/classifications/technologies-ds1000-all-$year
    OUTPUT=usage-$year.txt
    OUTPUT=data/usage-$year.txt
    python collect_usage_data.py -c $CORPUS -m maturity -t $CLASSIFICATION -o $OUTPUT #--limit 9999
    echo
done
fi

