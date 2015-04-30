# PGA
# create unlabeled invention keyterm annotation files for Chinese patents
# We will use a random corpus of chinese patents, broken down by year.
# We need to get the files.txt list for each yearly subcorpus and extract the 20 tail files
# to get a sample of 100 patents across 5 years. 

YEAR_LIST="1998 2000 2002 2004 2006"
CORPUS="ln-cn-all-600k"
CORPUS_PATH="/home/j/corpuswork/fuse/FUSEData/corpora/$CORPUS/subcorpora"
KEYTERMS_PATH="/home/j/anick/patent-classifier/ontology/roles/data/annotation/keyterms"
FILE_COUNT=20

# files.ln-cn-all-600k.1998.tail.20


#: <<'MYCOMMENT'

for YEAR in $YEAR_LIST; do 
    YEAR_PATH=$CORPUS_PATH/$YEAR
    echo "YEAR_PATH: $CORPUS_PATH/$YEAR"
    
    KEYTERMS_YEAR_FILELIST=$KEYTERMS_PATH/files.$CORPUS.$YEAR.tail.$FILE_COUNT
    echo "KEYTERMS_YEAR_FILELIST: $KEYTERMS_PATH/files.$CORPUS.$YEAR.tail.$FILE_COUNT"
    # create the filelist for a year
    # tail -20 /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/1998/config/files.txt > files.ln-cn-all-600k.1998.tail.20
    FILE_LIST_FILE=$KEYTERMS_PATH/files.$CORPUS.$YEAR.tail.$FILE_COUNT
    echo "FILE_LIST_FILE: $KEYTERMS_PATH/files.$CORPUS.$YEAR.tail.$FILE_COUNT"

    OUTPUT_DIR=$KEYTERMS_PATH/$CORPUS.$YEAR
    echo "OUTPUT_DIR: $KEYTERMS_PATH/$CORPUS.$YEAR"
    tail -$FILE_COUNT $YEAR_PATH/config/files.txt > $FILE_LIST_FILE
    # create the annotation file for the year
    #python create_annotation_files.py --inventions -c /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/1998 -f  /home/j/anick/patent-classifier/ontology/roles/data/annotation/keyterms/cn_test_file_1998 -o /home/j/anick/patent-classifier/ontology/roles/data/annotation/keyterms/cn_test_1998
    # create the annotation corpus for the year
    python create_annotation_files.py --inventions -c $YEAR_PATH -f $FILE_LIST_FILE -o $OUTPUT_DIR

done

#MYCOMMENT

# concatenate yearly unlab files into a single unlab file
CONCAT_DIR=$KEYTERMS_PATH/$CORPUS
mkdir $CONCAT_DIR
touch $CONCAT_DIR/annotate.inventions.unlab.txt
# clear out the target file in case it already has content from a previous run
> $CONCAT_DIR/annotate.inventions.unlab.txt

for YEAR in $YEAR_LIST; do 
    YEARLY_DIR=$KEYTERMS_PATH/$CORPUS.$YEAR
    # use a temp file since you cannot cat from a file into the same file
    mv $CONCAT_DIR/annotate.inventions.unlab.txt $CONCAT_DIR/temp
    cat $CONCAT_DIR/temp $YEARLY_DIR/annotate.inventions.unlab.txt > $CONCAT_DIR/annotate.inventions.unlab.txt
    
done


 

