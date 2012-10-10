rdg_path=$1
version=$2

test_path=$rdg_path/test
mallet_out_file=$test_path/utest.$version.MaxEnt.out
scores_nr_file=$test_path/utest.$version.MaxEnt.out.y.nr
scores_nr_noexp_file=$test_path/utest.$version.MaxEnt.out.scores


#cat utest.3.MaxEnt.out | egrep '^[0-9]'  | cut -f1,5 | sort -k2 -nr > utest.3.MaxEnt.out.y.nr
#cat utest.3.MaxEnt.out.y.nr | grep -v "E-" > utest.3.MaxEnt.out.y.nr.noexp

cat $mallet_out_file | egrep '^[0-9]'  | cut -f1,5 | sort -k2 -nr > $scores_nr_file
cat $scores_nr_file | grep -v "E-" > $scores_nr_noexp_file

echo "[tech_scores]Created $scores_nr_noexp_file"
