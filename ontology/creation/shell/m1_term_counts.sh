# m1_term_counts.sh
# creates a directory of files of the form <term>\t<count>
# user    6
# system  5
# musical tracks  5
# ...
# where term is a term appearing in the abstract, title, or summary of a phr_feats_file and count is the number
# of occurrences.  There is a minimum count of 3 imposed using filter_uc2.py

# arg1: full path of file.txt file, which is of the form <year>\t<source_file>\t<processed_file>
# processed file is the location of the file after it has gone through some processing.  It is of the form
# <year>/<file> (without .gz) and should be appended to the appropriate root path to get the full path.
# arg2: the root path for the processed files
# arg3: the directory to contain the output files, usually corresponding to the year (first field in files.txt file)

# Test the file using
# sh m1_test.sh
# or 

# This call uses the set of NYU cs patents, whose dates correspond to publication year, not application year
# sh m1_term_counts.sh /home/j/anick/patent-classifier/ontology/creation/data/patents/cs_2002_subset/config/files.txt /home/j/anick/patent-classifier/ontology/creation/data/patents/cs_2002_subset/data/d3_phr_feats/01/files /home/j/anick/patent-classifier/ontology/creation/data/patents/cs_2002_subset/data/m1_term_counts

# This call uses a larger set of cs files from BAE with application year in first column of files.txt file.  This will
# give more accurate time series information.
# sh m1_term_counts.sh /home/j/corpuswork/fuse/FUSEData/corpora/ln-cs-500k/subcorpora/1995/config/files.txt  /home/j/anick/patent-classifier/ontology/creation/data/patents/cs_500k/data/d3_phr_feats/01/files /home/j/anick/patent-classifier/ontology/creation/data/patents/cs_500k/data/m1_term_counts

# Note.  In case the true year of publication is different from the year included within the path of the file,
# we will use the
# year field for creating the output path and the year/file field for creating the input path. 
# So the output will be correctly labeled by year.

FILELIST=$1
INROOT=$2
OUTROOT=$3
# SECTIONS should be ta (title abstract) or tas (title abstract summary)
SECTIONS=$4

CODEDIR="/home/j/anick/patent-classifier/ontology/creation"

file_no=0
# read three tab separated fields from the FILELIST file
while read YEAR SOURCE YEAR_FILE; do
    #echo "input: $YEAR, $YEAR_FILE"
    file_no=`expr $file_no + 1`
    outfile=$(basename $YEAR_FILE)
    outdir=$OUTROOT/$YEAR
    # make sure outdir exists before using it
    mkdir -p $outdir
    # output file fully specified
    outpath=$outdir/$outfile

    # assume input file is compressed
    infile=$INROOT/$YEAR_FILE.gz

    #echo "output: $outfile, $outpath, $infile"
    #echo "file $file_no: $outpath"

    if [ $SECTIONS == "ta" ]
	then 
	#echo "running: gunzip -c  $infile |  egrep 'ABSTRACT|TITLE' | cut -f3 | sort | uniq -c | sort -nr | python $CODEDIR/filter_uc2.py 1 > $outpath   "
	gunzip -c  $infile |  egrep 'ABSTRACT|TITLE' | cut -f3 | sort | uniq -c | sort -nr | python $CODEDIR/filter_uc2.py 1 > $outpath

    elif [ $SECTIONS == "tas" ]
	then
	gunzip -c  $infile |  egrep 'ABSTRACT|TITLE|SUMMARY' | cut -f3 | sort | uniq -c | sort -nr | python $CODEDIR/filter_uc2.py 3 > $outpath

    else
	echo "missing SECTIONS parameter (ta or tas)"
	
    fi

done < $FILELIST