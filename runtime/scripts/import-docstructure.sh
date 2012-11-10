#!/bin/csh -f

# Script to import tries code from its git repository in
# ~marc/Dropbox/FUSE/document-processing/structure/git and add it to ../../utils.

set source_dir = '/home/j/marc/Dropbox/FUSE/document-processing/structure/git'
set source_dir = '/Users/marc/Dropbox/FUSE/document-processing/structure/git'
set target_dir = '/home/j/marc/Desktop/FUSE/code/patent-classifier/utils'
set target_dir = '/Users/marc/Documents/fuse/git/patent-classifier/utils'

echo
echo "IMPORTING..."
echo

cd $source_dir
echo ./utils/export.sh $target_dir
./utils/export.sh $target_dir

echo 
echo "UNPACKING..."
echo

echo cd $target_dir
cd $target_dir

# this assumes we are in ../../utils directory
# must change this if $target_dir is changed
../runtime/scripts/unpack.sh docstructure
