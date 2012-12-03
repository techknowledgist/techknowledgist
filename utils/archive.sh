#!/bin/csh -f

# Shell script to export a directory to a given destination. Running it from its parent
# directory will create an archive of the git repository with the following name 
#
#     patent-classifier-DATE:TIME-SHA1.tar
#
# where SHA1 has the first seven digits of the SHA-1 hash of the current head. This
# assumes (I think) that we are currently on the master branch since what is archived is
# the master branch. If not, the SHA1 value may be useless to find the code in git. Also
# note that non-commited changes will not be logged and will further reduce the likelyhood
# of re-creating the code.
#
# To inform the user on what is exported, the script prints the archive created and the
# git status on the working directory.


set date = `date +"%Y%m%d:%H%M"`
set head = `git rev-parse --short HEAD`
set archive = "patent-classifier-$date-$head.tar"

echo ; echo "ARCHIVING patent-classifier"

echo ; echo "GIT STATUS:"
git status -bs

echo ; echo "CREATING ARCHIVE $archive..."
git archive master --prefix="patent-classifier/" > $archive
gzip $archive
mv $archive.gz /local/chalciope/marc/fuse
ls -l /local/chalciope/marc/fuse
