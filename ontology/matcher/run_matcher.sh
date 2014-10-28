CORPORA=/home/j/corpuswork/fuse/FUSEData/corpora/wos-cs-520k/subcorpora

for year in 1997 1998 1999 2000 2001 2002 2003 2004 2005 2006 2007;
do
    echo $ python run_matcher.py --corpus $CORPORA/$year --output maturity
    python run_matcher.py --corpus $CORPORA/$year --output maturity
done
