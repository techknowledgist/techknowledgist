#!/bin/csh -f

# Script to create a backup of the patent-classifier directory. It is not intended to
# create a versioned release, nor does it attempt to be complete, just complete enough so
# that the code will run. Only works on chalciope and if you have write access to
# /local/chalciope.

set version = `date +"%Y%m%d-%H%M%S"`
set target = /local/chalciope/marc/fuse/patent-classifier-${version}.tar

cd /home/j/marc/Desktop/FUSE/code
rm patent-classifier/runtime/data/tmp/*
tar cfp $target patent-classifier/documents
tar rfp $target patent-classifier/examples
tar rfp $target patent-classifier/runtime
tar rfp $target patent-classifier/utils
tar rfp $target patent-classifier/ontology/creation/*py
tar rfp $target patent-classifier/ontology/creation/*sh
tar rfp $target patent-classifier/ontology/creation/*txt
tar rfp $target patent-classifier/ontology/annotation/??/phr_occ.lab
tar rfp $target patent-classifier/ontology/selector/*.py
tar rfp $target patent-classifier/ontology/selector/*.txt
gzip $target
ls -al /local/chalciope/marc/fuse

# okay, let's add the update of the mirror, so I do not forget updating it once in a while
cd /local/chalciope/marc/fuse/patent-classifier.git
git remote update
