# term_features.sh
# Given the phr_feats files on FUSE net, create a file for each patent containing
# term feature-value count
# for features of interest: head, prev_V, prev_Npr, prev_Jpr, prev_J

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

    # if output file already exists, do not overwrite
    if [ -f $outpath ];
    then
	#echo "File $outpath exists.  NOT overwriting!"
	# no op
	:
    else
	#echo "Creating $outpath."




    # assume input file is compressed
    infile=$INROOT/$YEAR_FILE.gz



    #echo "output: $outfile, $outpath, $infile"
    #echo "file $file_no: $outpath"

    if [ $SECTIONS == "ta" ]
	then 
	#echo "running: gunzip -c  $infile |  egrep 'ABSTRACT|TITLE' | cut -f3 | sort | uniq -c | sort -nr | python $CODEDIR/filter_uc2.py 1 > $outpath   "
	gunzip -c  $infile |  egrep 'ABSTRACT|TITLE' | python $CODEDIR/term_features.py | sort | uniq -c | sort -nr | python $CODEDIR/reformat_uc2.py > $outpath

    elif [ $SECTIONS == "tas" ]
	then
	gunzip -c  $infile |  egrep 'ABSTRACT|TITLE|SUMMARY' | python $CODEDIR/term_features.py | sort | uniq -c | sort -nr | python $CODEDIR/reformat_uc2.py > $outpath

    else
	echo "missing SECTIONS parameter (ta or tas)"
	
    # end loop for section option
    fi

    # end the loop for each individual file
    fi

done < $FILELIST