Note that some of these utilities are actually exported from other repositories and that
they are not maintained here. These also do not need to be checked into the git
repository. This is the case, for example, for docstructure and tries.

To export the document structure parser, do something like this:

% cd ~marc/Dropbox/FUSE/document-processing/structure/git
% ./utils/export.sh /home/j/corpuswork/fuse/code/utils
% cd /home/j/corpuswork/fuse/code/utils
% mv docstructure docstructure-saved
% mv docstructure-20120922 docstructure

The tries utilities is taken from my utilities repository. To import from that repository,
use the scripts in runtime/utils.

Marc Verhagen
marc@cs.brandeis.edu
September 2012
