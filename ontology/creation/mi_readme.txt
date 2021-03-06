Co-occurrence analysis for term-term and term-verb relationships

-rw-r--r-- 1 anick grad 1832 Dec 17 21:37 m1_test.sh
-rw-r--r-- 1 anick grad 3283 Dec 18 21:22 m1_term_counts.sh
-rw-r--r-- 1 anick grad 1832 Dec 18 21:28 run_m1_term_counts.sh
-rw-r--r-- 1 anick grad 1321 Dec 18 22:16 term_verb.sh
-rw-r--r-- 1 anick grad 1836 Dec 19 16:36 run_term_verb.sh

-rw-r--r-- 1 anick grad  4902 Dec 11 09:17 dispersion.py
-rw-r--r-- 1 anick grad   819 Dec 11 22:30 filter_uc2.py
-rw-r--r-- 1 anick grad 71737 Dec 12 08:19 terms_db.py
-rw-r--r-- 1 anick grad  1475 Dec 18 22:04 term_verb.py
-rw-r--r-- 1 anick grad 11214 Dec 18 23:01 mi.py
-rw-r--r-- 1 anick grad  6237 Dec 19 16:28 term_verb_count.py
-rw-r--r-- 1 anick grad  4206 Dec 19 17:56 mi_diff.py
-rw-r--r-- 1 anick grad   614 Dec 19 18:27 reformat_uc1.py

STEPS
(1) Create the phr_feats file for years of data
(2) Create a set of directories where target data will go under <database_name>/data/
e.g. m1_term_counts  m1_term_counts_tas  m1_term_verb_tas  m2_mi  m2_mi_tas  m2_tv

directory contents (after running programs):

m1_term_counts  (one subdirectory per year containing term count info for all .xml files for that year)
m1_term_counts_tas (created including lines from the summary sections of patents)
m1_term_verb_tas (one subdirectory per year containing term/verb count info for all .xml files for that year)
m2_mi (one file per year [<year>.mi] containing mutual info and freq info for cooccurring pairs of terms)
m2_mi_tas  
m2_tv (one file per year): 
      .mi term/verb with MI info
      .tcmi term/category with MI info 
      .vc term with category frequencies for each category

Programs to run:      
run_m1_term_counts.sh	populates m1_term_counts for multiple years
run_term_verb.sh	populates m1_term_verb for mulitple years
python 
import term_verb_count	
term_verb_count.test_cs_500k()		creates .mi summary of term_verb MI/freqs for each year
					running time ~ 40 minutes
		term		verb		mi*freq		mi	    pair   term      verb
	e.g. subordinates    following       0.000000        0.024042        1       2       5091

term_verb_count.run_dir2mi_tc_cs_500k()		creates .tcmi summary of term_cat MI/freqs for each each year
						rerun this after changing verb.cat.en.dat
						running time ~ 35 minutes
		term		cat	mi*freq		mi    	      pair	term	cat
	e.g.	drawbacks       a       -0.000000       -0.293545       1       24      8547


term_verb_count.run_mi2vcat()		     creates .vc summary of term cats w/counts for each category per term
					     depends on .tcmi files
					     running time ~ 6 minutes
              term            cats   a        c      g       n       o       p
        e.g. circuitry       acgop   3       165     2       0       6       41

import mi_diff
mi_diff.run_tv_diff()			creates .mi.diff  difference in k3 (mi*freq) between prev and current year
					depends on .tcmi files
					running time ~ 20 secs

To get diff sorted by adj_change difference, use column 7:
cat 1996.tcmi.diff | sort -nr -k7 -t" " > 1996.tcmi.diff.k7

todo: script to sort by k7
determine top cat for each term and output sorted terms by cat (only top cat for each term)

run_term_uc.sh
For all xml files in m1_term_counts_tas, create a single file in m2_mi_tas which counts the 
number of docs each term occurs in.
File name is <year.uc>
Format:
invention       12425

term_verb_count.run_dir2tfc()   Creates .tfc files per year in m2_tv
This combines .uc (doc freq) with .vc (primary category freq) data
term                    cat    uc_freq  cat_freq
matrix multiplication   t       2       3

mi_diff.run_tfc_diff()   Creates a tfc.diff file from .tfc which gives year-previous year differences
term			 year	 c_cat	l_freq  c_freq  % change        adj_change      diff cat change? l_cat  count  c_cat    count
system performance      1996    |a      32      68      2.09090909091   10.8924934009   36   n       a       177     a       257

Note that the counts for freq and cat count are based on different criteria.  The freq is # docs in which term occurs at
least n times (where n = 3).   The cat counts are based on the number of times a term occurs with a diagnostic verb for
the primary category of the term.

sort_tfc_diff.sh  sorts the tfc.diff files by k7 (adjusted change)

----------------------------------------------------------------------------------------------------
details:
run_m1_term_counts.sh
(replaces m1_test.sh)
Calls m1_term_counts.sh for a set of years and directories
Input: fuse data
/home/j/corpuswork/fuse/FUSEData/corpora/ln-cs-500k/subcorpora/$YEAR/config/files.txt 
/home/j/corpuswork/fuse/FUSEData/corpora/ln-cs-500k/subcorpora/$YEAR/data/d3_phr_feats/01/files
Output: m1_term_counts
/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_500k/data/m1_term_counts    

m1_term_counts.sh
Creates a directory of files of the form <term>\t<count>
Called by run_m1_term_counts.sh
Assumes input files (phr_feats files) are compressed
Extracts phr_feats lines from abstract, title, and (optionally) summary and sums over the 
number of occurrences of each term in a file.

run_term_verb.sh
Calls term_verb.sh for a series of years
Input:
fuse files.txt, d3_phr_feats
/home/j/corpuswork/fuse/FUSEData/corpora/ln-cs-500k/subcorpora/$YEAR/config/files.txt 
/home/j/corpuswork/fuse/FUSEData/corpora/ln-cs-500k/subcorpora/$YEAR/data/d3_phr_feats/01/files 
Output:
m1_term_verb
/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_500k/data/m1_term_verb 

term_verb.sh
Called by run_term_verb.sh
Runs term_verb.py over the phr_feats lines in title, abstract and (optionally) summary to extract term and verb.
Verb is the dominating verb, or verb_prep combination for the term, as captured in feature prev_V or prev_V2, depending
on the feature set used when phr_feats was created.

The option (ta or tas) determines whether summary sections are included in the output.  In this case, tas was chosen.

Creates a file in m1_term_verb/<year> for each doc containing the count of the pair of term and verb
e.g.
bit     selected_from   2
audio channel field     comprises       2

----
term_verb_count.py

dir2mi (called by test_cs_500k)
Creates a summary tsv file per year of term-verb pair statistics (<year>.mi):
fields: term, verb, mi*doc_freq, mi, pair doc_freq, term doc_freq, verb doc_freq

Input
 "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_500k/data/m1_term_verb"
Output
"/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_500k/data/m2_tv"
e.g.
camera  calibrate       0.000000        0.095107        1       104     50
digital tokens  produce 0.648656        0.195265        10      17      1860

Other files can be derived from .mi files
1995.mi.k3:  sort -nr -k3

run_mi2vcat() runs mi2vcat for a range of years.
Categorize terms according to the verbs they occur with.
verb.cat.en.dat.sorted contains a list of 118 inflected verbs along with the semantic category of 
the direct object (or object of included preposition).

Categories of verbs: /// update this
a affected
c component (something used in something else)
g goal
n name (something called or named as)
p product (something produced or provided)

The output is a file of terms along with their categories and doc_freq for each category.
doc_freq is not the right word since if a term occurs with 2 different verbs of the same category
in the same doc, the doc will be counted twice.  It's really a count of unique doc_verb pairs for the 
term in the category.

term_count2vcat

Add the verb category to each verb in the term_verb_counts files, creating a parallel directory
with identical files but keeping only lines with a categorized verb and replacing the verb with the category 
and removing the count field.  Duplicates of the same term and category are removed.
e.g.
operating system        called  1
=>
operating system        n  

----
# For role ontology labeling
run_term_features.sh
Creates a .xml file for corresponding patent phr_feats files, containing term, feature, count
for features of interest: last_word, prev_V, prev_Npr, prev_J, prev_Jpr
TODO: add feature prev_VNP

python:
term_verb_count.run_dir2features_count()
Creates a .tf file per year in /home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-all-600k/data/tv
Gives the freq and prob of term feature pair for terms occurring with the seed features in seed.cat.en.dat
# e.g. terminals       prev_Npr=plurality_of   29      0.001819

# TBD: Make this into a script
Extract the verb features only into .tv file
cat 1997.tf | cut -f1,2,3 | grep prev_V | sed -e 's/prev_V=//' > 1997.tv 
cat 2007.tf | cut -f1,2,3 | grep prev_V | sed -e 's/prev_V=//' > 2007.tv 

#term category info
term_verb_count.run_tv2tc()
Processing dir: 1997
Completed: 1997.tc in /home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-all-600k/data/tv

# sorted by prob, with freq 1 removed
cat 1997.tc.k5 | egrep -v '   1       ' > 1997.tc.k5.gt2

term_verb_count.run_tc2st()
Process the output of run_tv2tc to create a set of seed terms for feature category learning.
Choose terms for which the category threshold > min_category_prob and pair freq (term and category) > min_pair_freq 

To see learned associations between features and classes:
cat 1998.fc.prob.k3 | egrep ' t       ' | more

candidate coercion verbs:
have medium probs (no preps)
cat 1998.fc.prob.k3 | grep prev_V | egrep -v '=.*_' | egrep '0\.[23456]' | sort -k1,2 -t'       ' | more
