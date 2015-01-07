# tag2json.sh
# create a file for a subcorpus and year containing sentence and chunk info for elasticsearch indexing

# NOT FINISHED!

# based on term_features.sh
# Given the phr_feats files on FUSE net, create a file for each patent containing
# term feature-value count
# for features of interest: head, prev_V, prev_Npr, prev_Jpr, prev_J

FILELIST=$1
INROOT=$2
OUTFILE=$3
# SECTIONS should be ta (title abstract) or tas (title abstract summary)
SECTIONS=$4

CODEDIR="/home/j/anick/patent-classifier/ontology/roles"

file_no=0
# read three tab separated fields from the FILELIST file
while read YEAR SOURCE YEAR_FILE; do
    #echo "input: $YEAR, $YEAR_FILE"
    file_no=`expr $file_no + 1`

    # assume input file is compressed
    infile=$INROOT/$YEAR_FILE.gz

    echo "[tag2json]output: $OUTFILE, input: $infile"

    # use 2.7 for json modules.
    ###python2.7 $CODEDIR/tag2json.py $infile $outpath $SECTIONS
    # end the loop for each individual file

    # for testing, limit number of files to process per year
    if [ $file_no -gt 2 ] 
	then exit
	fi

done < $FILELIST

# example call to tag2chunk in python
#         tag2chunk.Doc(file_in, file_out, year, rconfig.language,
#                      filter_p=filter_p, chunker_rules=chunker_rules, compress=True)