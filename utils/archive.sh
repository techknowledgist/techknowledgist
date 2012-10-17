#!/bin/csh -f

# Shell script to export a directory to a given destination. Running it from its parent
# directory will create an archive of the git repository with the following name 
#
#     patent-classifier-SHA1.tar
#
# where SHA1 is the SHA-1 hash of the current head. This assumes (I think) that we are
# currently on the master branch since what is archived is the master branch. If not, the
# SHA1 value may be useless to find the code in git. Also note that non-commited changes
# will not be logged and will further reduce the likelyhood of re-creating the code.
#
# To inform the user on what is exported, the script prints the archive created and the
# git status on the working directory.


set head = `git rev-parse HEAD`
set archive = "patent-classifier-$head.tar"

echo ; echo "RUNNING DOCUMENT STRUCTURE EXPORTER"

echo ; echo "GIT STATUS:"
git status -bs

echo ; echo "CREATING ARCHIVE $archive..."
git archive master --prefix="patent-classifier/" > $archive
