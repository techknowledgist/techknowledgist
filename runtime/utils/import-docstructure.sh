#!/bin/csh -f

set source_dir = '/home/j/marc/Dropbox/FUSE/document-processing/structure/git'
set target_dir = '/home/j/corpuswork/fuse/code/patent-classifier/utils'

echo
echo "RUNNING DOCUMENT STRUCTURE IMPORTER"
echo

echo cd $source_dir
cd $source_dir
echo ./utils/export.sh $target_dir
./utils/export.sh $target_dir

echo 
echo "UNPACKING DOCUMENT STRUCTURE CODE"
echo

echo cd $target_dir
cd $target_dir
echo rm -rf docstructure
rm -rf docstructure
echo tar xfp docstructure-*.tar
tar xfp docstructure-*.tar
echo mv docstructure-*.tar docstructure
mv docstructure-*.tar docstructure
