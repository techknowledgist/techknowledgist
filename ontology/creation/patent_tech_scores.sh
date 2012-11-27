# patent_tech_scores.sh
# Produce scores by doc and across docs for probability of phrase being a technology term.
# pull out the scores from the mallet out file for the category of interest: technolology = y
#
# sh patent_tech_scores.sh /home/j/corpuswork/fuse/code/patent-classifier/ontology/creation/data/patents 2 en

# Modified 11/19/12 PGA to merge a step

patent_path=$1
version=$2
language=$3

test_path=$patent_path/$language/test
mallet_out_file=$test_path/utest.$version.MaxEnt.out
all_doc_scores_file=$test_path/utest.$version.MaxEnt.out.doc_scores
# Next file no longer created (11/19/12 PGA)
scores_nr_file=$test_path/utest.$version.MaxEnt.out.y.nr
# Name of next file changed (added .nr 11/19/12 PGA)
doc_scores_nr=$test_path/utest.$version.MaxEnt.out.doc_scores.nr
avg_scores=$test_path/utest.$version.MaxEnt.out.avg_scores

cat $mallet_out_file | egrep '^[0-9]'  > $all_doc_scores_file

# capture the column that contains the value for the technology = "y" in mallet output file
score_col=`python find_mallet_field_value_column.py $all_doc_scores_file y`
echo "score is found in column $score_col of $all_doc_scores_file"
# create a file with sorted scores (where scores are per document)
# cat $all_scores_file | cut -f1,$score_col | sort -k2 -nr > $scores_nr_file
# Remove entries containing an exponent - these are too small to be of interest 
#cat $scores_nr_file | grep -v "E-" > $scores_nr_noexp_file
# merge the above steps into a single pipe
cat $all_doc_scores_file | cut -f1,$score_col |  grep -v "E-" | sort -k2 -nr > $doc_scores_nr
echo "[tech_scores]Created $scores_nr_noexp_file"

# NOTE, may need parts of the following depending on how sum_scores works (MV, 20121127)
# Version of python needed was 2.5, which caused problems for systems where the default
# Python version was lower. Either needed to add a parameter to the script, or remove use
# of defaultdict in sum_scores.py, did the latter.
# echo "python sum_scores.py $scores_nr_noexp_file $scores_nr_noexp_file.sum"
# python sum_scores.py $scores_nr_noexp_file $scores_nr_noexp_file.sum

# Now produce a single score per phrase by averaging over document occurrences.
# NOTE: version of python is system dependent!
# For pasiphae we have to specify python26.  But it is the default on fusenet.
# This allows us to use defaultdict in the python script.
if [[ $(hostname) = 'pasiphae' ]]
then 
    echo "[patent_tech_scores.sh]Running python26 for sum_score.py"
    python26 sum_scores.py $doc_scores_nr $avg_scores
else
    echo "[patent_tech_scores.sh]Running python for sum_score.py"
    python sum_scores.py $doc_scores_nr $avg_scores
fi

# insert tab in emacs using ctr-q <tab>
cat $avg_scores | sort -k2,2 -nr -t"	" > $avg_scores.nr
echo "[tech_scores]Sorted average scores in: $avg_scores.nr"
