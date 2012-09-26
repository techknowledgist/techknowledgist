#!/bin/csh -f

# Script to create a backup of the entire patent-classifier directory. It is not intended
# to create a versioned release, it does however contain a full git repository with
# staging area. Only works on chalciope.

set version = `date +"%Y%m%d-%H%M%S"`
set target = /local/chalciope/marc/fuse/patent-classifier-${version}.tar

cd /home/j/corpuswork/fuse/code
rm patent-classifier/runtime/data/tmp/*
tar cfp $target patent-classifier
gzip $target
ls -al /local/chalciope/marc/fuse
