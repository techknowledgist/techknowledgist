#!/bin/sh
# sh /home/j/anick/fuse/cat_phr.sh /home/j/anick/fuse/data/patents/en/phr_occ /home/j/anick/fuse/data/patents/tmp/en
# sh /home/j/anick/fuse/cat_phr.sh /home/j/anick/fuse/data/patents/de/phr_occ /home/j/anick/fuse/data/patents/tmp/de

# Creates summary files for the chunk output, creates lists summed over years:
#
#    $output_dir/phr_occ.all  all instances
#    $output_dir/phr_occ.lab  all chunks, sorted by frequency, formatted for annotation
#    $output_dir/phr_occ.uct  all chunks, sorted by frequency, frequency added in first column


input_dir=$1
output_dir=$2

# initialize output files
:> $output_dir/phr_occ.uct
:> $output_dir/phr_occ.all


#<<COMMENT


for f in $input_dir/*/*; do
    echo $f
    cat $f | cut -f3  >> $output_dir/phr_occ.all
done

#COMMENT

cat $output_dir/phr_occ.all | sort | uniq -c | sort -nr | python26 /home/j/anick/fuse/reformat_uc.py > $output_dir/phr_occ.uct

echo "created $output_dir/phr_occ.uct" 

#COMMENT

cat $output_dir/phr_occ.uct | sed -e 's/^[0-9]*	/	/' > $output_dir/phr_occ.lab
echo "created $output_dir/phr_occ.lab" for labeling
 
