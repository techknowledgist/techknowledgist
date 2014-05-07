This directory contains files relevant to the English maturity score self
evaluation.


1. Selecting terms to evaluate

The file terms-candidates.txt was created May 4th 2014 and contains a batch of
candidate terms to be used for evalution. It has the following characteristics:

- the terms occur 200 or 201 times in the corpus
- the corpus used was the ln-us-all-600/subcorpora/2000 corpus
- the terms have a technology score of higher than 0.5

This list was created with the function find_terms_for_us_maturity_evaluation2()
in ontology/indexer/get_terms() from commit 0c63a42 (v0.4-62-g0c63a42). It has
31 elements.

The file terms-selected.txt is based on terms-candidates.txt, but with obvious
non-technologies filtered out. In addition, some terms for which it was expected
that they would be hard to annotate were removed. The file has 16 elements. The
goal is to have at least 10 terms since that is the minimal number to use for
the Pearson Correlation.


2. Extract all locations for these terms

The file terms-locations.txt is created with ontology/indexer/get_locations.py
using the --filter option and using terms-selected.txt as the input (which is
actually one of the defaults). Again, the git commit was 0c63a42. This script
also filters out a few more terms and at the end of this step there are only
twelve terms left, which is still over the minimum threshold of 10.

Here is a comment from that file that hints at a problem with the maturity
scoring:

# Note that filter test number (2) above is a bit puzzling since we start off
# with 200 occurrences, this needs to be investigated. As a first result, it
# turns out that if you remove the terms that occur in fewer than 4 documents
# then the terms with a maturity score of -1 also disappear. This seems to
# suggest that the code to find maturity scores throws out some cases where
# there are enough occurrences to work with.


3. Create annotation file

TBA
