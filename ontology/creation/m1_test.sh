# script to run m1_term_counts.sh with set parameters
#sh m1_test.sh

# Peter's cs_2002_subset of 100 patents
#sh m1_term_counts.sh /home/j/anick/patent-classifier/ontology/creation/data/patents/cs_2002_subset/config/files.txt /home/j/anick/patent-classifier/ontology/creation/data/patents/cs_2002_subset/data/d3_phr_feats/01/files /home/j/anick/patent-classifier/ontology/creation/data/patents/cs_2002_subset/data/m1_term_counts

# Marc cs 284k files from 1980 to 2007
#sh m1_term_counts.sh /home/j/marc/Desktop/fuse/code/patent-classifier/ontology/creation/data/patents/201306-computer-science/config/files.txt /home/j/marc/Desktop/fuse/code/patent-classifier/ontology/creation/data/patents/201306-computer-science/data/d3_phr_feats/01/files /home/j/anick/patent-classifier/ontology/creation/data/patents/cs_284k/data/m1_term_counts

# This uses a larger set of cs files from BAE with application year in first column of files.txt file.  This will
# give more accurate time series information.
#sh m1_term_counts.sh /home/j/corpuswork/fuse/FUSEData/corpora/ln-cs-500k/subcorpora/1995/config/files.txt /home/j/corpuswork/fuse/FUSEData/corpora/ln-cs-500k/subcorpora/1995/data/d3_phr_feats/01/files /home/j/anick/patent-classifier/ontology/creation/data/patents/cs_500k/data/m1_term_counts

# loop over the years for which we have data
YEAR=1996
while [ $YEAR -le 2007 ] ; do
#while [ $YEAR -le 1995 ] ; do
    echo "year: $YEAR"

    sh m1_term_counts.sh /home/j/corpuswork/fuse/FUSEData/corpora/ln-cs-500k/subcorpora/$YEAR/config/files.txt /home/j/corpuswork/fuse/FUSEData/corpora/ln-cs-500k/subcorpora/$YEAR/data/d3_phr_feats/01/files /home/j/anick/patent-classifier/ontology/creation/data/patents/cs_500k/data/m1_term_counts ta

    YEAR=$[ $YEAR + 1 ]
done

