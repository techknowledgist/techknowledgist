#!/bin/sh

# old version:
# sh /home/j/anick/fuse/cat_phr.sh /home/j/anick/fuse/data/patents/en/phr_occ /home/j/anick/fuse/data/patents/en/ws
# sh /home/j/anick/fuse/cat_phr.sh /home/j/anick/fuse/data/patents/de/phr_occ /home/j/anick/fuse/data/patents/de/ws

# 10/7/12 PGA changed input parameters to patents_path, language
# sh /home/j/anick/fuse/cat_phr.sh /home/j/anick/fuse/data/patents /home/j/anick/fuse/data/patents/en/ws

patents_path=$1
language=$2
input_phr_occ_dir=$patents_path/$language/phr_occ
input_phr_feats_dir=$patents_path/$language/phr_feats
output_dir=$patents_path/$language/ws

echo "[cat_phr.sh]input_phr_occ_dir: $input_phr_occ_dir, input_phr_feats_dir: $input_phr_feats_dir, output_dir: $output_dir"

# initialize output files
:> $output_dir/phr_occ.uct
:> $output_dir/phr_occ.all
:> $output_dir/phr_feats.all

echo "Finished initialization"
#<<COMMENT

# merge all phr_occ lines into one file (phr_occ.all)
for f in $input_phr_occ_dir/*/*; do
    
    echo $f
    cat $f | cut -f3  >> $output_dir/phr_occ.all
done
echo "[cat_phr.sh]Created $output_dir/phr_occ.all"

#<<COMMENT
# merge all phr_feats lines into one file (phr_feats.all)
for f in $input_phr_feats_dir/*/*; do
    echo $f
    cat $f >> $output_dir/phr_feats.all
done
echo "[cat_phr.sh]Created $output_dir/phr_feats.all"

#COMMENT

# count up the number of phr_occ occurrences
#cat $output_dir/phr_occ.all | sort | uniq -c | sort -nr | python /home/j/anick/fuse/reformat_uc.py > $output_dir/phr_occ.uct
cat $output_dir/phr_occ.all | sort | uniq -c | sort -nr | python reformat_uc.py > $output_dir/phr_occ.uct

echo "[cat_phr.sh]Created $output_dir/phr_occ.uct" 

#COMMENT

# Create a sorted list of possible technology phrases suitable for labeling (by y or n character in first position of each line)
cat $output_dir/phr_occ.uct | sed -e 's/^[0-9]*	/	/' > $output_dir/phr_occ.unlab
echo "[cat_phr.sh]Created $output_dir/phr_occ.lab" for labeling
echo "NOTE: You must place a (manually) labeled file phr_occ.lab into the workspace directory before proceeding to the next automated step (machine learning)!!"

# After labeling a subset of the lines in phr_occ.unlab, manually insert this file into the workspace subdirectory with the name phr_occ.lab

