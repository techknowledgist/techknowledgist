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

Categories of verbs:
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


