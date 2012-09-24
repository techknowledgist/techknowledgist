#!/bin/csh -f

set source_dir = '/home/j/marc/Dropbox/code/misc'
set target_dir = '/home/j/corpuswork/fuse/code/patent-classifier/utils'

echo
echo "IMPORTING TRIES CODE"
echo

echo cd $source_dir
cd $source_dir
echo ./export.sh tries $target_dir
./export.sh tries $target_dir

echo 
echo "UNPACKING TRIES CODE"
echo

echo cd $target_dir
cd $target_dir
echo rm -rf tries
rm -rf tries
echo tar xfp tries-*.tar
tar xfp tries-*.tar
echo mv tries-*.tar tries
mv tries-*.tar tries
