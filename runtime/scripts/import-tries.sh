#!/bin/csh -f

# Script to import tries code from its git repository in ~marc/Dropbox/code/misc and add
# it to ../../utils. 

set source_dir = '/home/j/marc/Dropbox/code/misc'
set target_dir = '/home/j/corpuswork/fuse/code/patent-classifier/utils'
set target_dir = '/home/j/marc/Desktop/FUSE/code/patent-classifier/utils'

echo
echo "IMPORTING..."
echo

echo cd $source_dir
cd $source_dir
echo ./export.sh tries $target_dir
./export.sh tries $target_dir

echo 
echo "UNPACKING..."
echo

echo cd $target_dir
cd $target_dir

# this assumes we are in ../../utils directory
# must change this if $target_dir is changed
../runtime/scripts/unpack.sh tries
