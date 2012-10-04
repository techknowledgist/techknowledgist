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

# okay, let's add the update of the mirror, so I do not forget updating it once in a while
cd /local/chalciope/marc/fuse/patent-classifier.git
git remote update
