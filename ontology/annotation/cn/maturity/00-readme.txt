This directory contains files relevant to the Chinese maturity score self
evaluation. This file is similar to ../../en/maturity/00-readme.txt, but lacks a
few of the background details.


1. Selecting terms to evaluate

The file terms-candidates.txt was created May 4th 2014 and contains a batch of
candidate terms to be used for evalution. It has the following characteristics:

- the terms occur 99, 100, 101, 102 or 103 times in the corpus
- the corpus used was the ln-cn-all-600/subcorpora/2000 corpus
- the terms have a technology score of higher than 0.5

This list was created with the function find_terms_for_cn_maturity_evaluation()
in ontology/indexer/get_terms() from commit gb1af98d (v0.4-65-gb1af98d). It has
37 elements.

The list was updated a bit later to include maturity scores, using git commit
f06661e (v0.4-70-gf06661e).

The file terms-selected.txt is based on terms-candidates.txt, but with obvious
non-technologies filtered out. The file has 28 elements. The files named
terms-selected-sili-1.txt and terms-selected-sili-2.txt were the files given to
Si Li for annotation and received back from her respectively.


2. Extract all locations for these terms

The file terms-locations.txt is created with ontology/indexer/find_locations.py
using the --filter option and using terms-selected.txt as the input (which is
actually one of the defaults). The git commit was 6cc8532 (v0.4-68-g6cc8532). At
the end of this step there are eighteen terms left.


3. Create annotation file

Used ontology/creation/step3_annotation.py to create the annotation file
annotate.maturity.cn.context.txt, which was then annotated with the tool 
ontology/annotation/tool/term_annotator.py using --maturity mode.

The results of the annotation is in annotate.maturity.cn.labels.txt. Labels were
added by Si Li.


4. Collect data and calculate Pearson's r

Use merge_results.py to create terms-merged.txt, which has both the counts and
the maturity scores.

Then use the calculator at

	http://www.socscistatistics.com/tests/pearson/

The result using all 18 data points is:

r = 0.174

This is a very weak positive correlation. 

The dataset contained one outlier where a 0 maturity score was paired with a
high annotation score. Removing this outlier raised the score to 0.5391, which
indicates a strong correlation.
