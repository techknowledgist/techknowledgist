# pull out the scores from the mallet out file for the category of interest: technolology = y
#
# sh patent_tech_scores.sh /home/j/corpuswork/fuse/code/patent-classifier/ontology/creation/data/patents 2 en

patent_path=$1
version=$2
language=$3

test_path=$patent_path/$language/test
mallet_out_file=$test_path/utest.$version.MaxEnt.out
all_scores_file=$test_path/utest.$version.MaxEnt.out.all_scores
scores_nr_file=$test_path/utest.$version.MaxEnt.out.y.nr
scores_nr_noexp_file=$test_path/utest.$version.MaxEnt.out.scores



cat $mallet_out_file | egrep '^[0-9]'  > $all_scores_file
# capture the column that contains the value for the technology = "y" in mallet output file
score_col=`python find_mallet_field_value_column.py $all_scores_file y`
echo "score is found in column $score_col of $all_scores_file"
cat $all_scores_file | cut -f1,$score_col | sort -k2 -nr > $scores_nr_file
cat $scores_nr_file | grep -v "E-" > $scores_nr_noexp_file

echo "[tech_scores]Created $scores_nr_noexp_file"

# version of python is system dependent!
python sum_scores.py $scores_nr_noexp_file $scores_nr_noexp_file.sum
#python sum_scores.py $scores_nr_noexp_file $scores_nr_noexp_file.sum

# insert tab in emacs using ctr-q <tab>
cat $scores_nr_noexp_file.sum | sort -k2,2 -nr -t"	" > $scores_nr_noexp_file.sum.nr
echo "[tech_scores]Summed, sorted scores in: $scores_nr_noexp_file.sum.nr"
