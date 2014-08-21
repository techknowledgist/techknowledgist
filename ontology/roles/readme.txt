This package includes several semi-independent functionalities:

I. Temporal feature analysis (Growth indicator feature extraction)

1. Determine a cohort of growth terms within a range of years.  The cohort is defined as a set of terms
which each first appears in a given year (where "first appears" means that it did not occur in the previous year) and
which satisfy a set of constraints regarding growth (frequency of occurrence in a given year).  Frequency is measured for
the phrase as a whole.  If it occurs as a subphrase of a longer phrase, this is not counted as an occurrence of the subphrase.

2. Use this growth cohort to determine which features cooccur with the cohort terms more than with other terms.  ie.
prob(feature|cohort term)/prob(feature|any term).  TBD: compute a cohort of terms that first appear in the same year as
the growth cohort but which do not meet the growth constraints and use this to predict growth-related features.

There are two kinds of features, external and head.  An external feature is one that occurs outside the phrase (prev_V, prevJ),
while the head feature refers to the head of the phrase itself (e.g. "system" for "operating system"), which in English is the
last_word feature.

3. Once a set of growth indicator features are determined, create a file with the indicator feature count for each term in a given year.

II. ACT Role detection

ACT Role detection attempts to classify a term as A(attribute), (C)omponent, or (T)ask.  This is primarily to allow the user 
interface to present terms according to their function.  Most terms are components, so this allows the attributes and tasks to be 
identified more easily.  Role detection is performed in several steps.  An initial (seed) set of relatively unambiguous features is used 
to label terms into one of the three categories.  These labeled terms are then used to build a classifier.   TBD: Do further feature 
selection on the set of terms used in the classifier.  It would be better to leave some terms unclassified, since the categories do not
cover all possible roles.

Polarity detection for attributes

For the set of terms identified as attributes in ACT classification, bootstrap a classifier from a seed feature set to label the
attributes as positive (worth increasing) or negative (worth decreasing).  TBD: Add a neutral category for terms that either have no
polarity (simply denote dimensions) and a multiple polarity for those that have multiple polarities depending upon context. 

Term specificity

By comparing the frequency of occurrence of terms in a domain corpus to that in a generic corpus (corpus composed of a random but
balanced set of docs from all domains of concern), we can measure the domain specificity of a term.  This is also useful for 
user interface, to separate out domain specific terms from generic ones.


To run the code:

We assume that documents are to be temporally labeled by application year (if patents) or by publication year (if research paper),  
We also assume that we have documents organized into subcorpora by domain and within year for each domain.  As a prior step to
running functions in this package, a corpus must be set up with a set of domains and a range of years.  Each subcorpus must be processed
to the point of creating feature files (d3_phr_feats) [See Marc Verhagen's code for documentation of the prerequisite steps]

The first step is to set up the directory structure needed to process the subcorpora and to populate the term_features directory. 
This directory has one file for each document in the domain/year.  It is a subset of the lines and features in the source phr_feats files, 
limited to the sections desired (e.g. title, asbstract, summary) and features of interest for the current tasks.

1. Create directory for corpus and populate term_features subdirectory and initial files in tv directory

Modify the values of FUSE_CORPUS_ROOT and LOCAL_CORPUS_ROOT in the script run_term_features.sh to correspond to
the fuse path where the corpus can be found (e.g. /home/j/corpuswork/fuse/FUSEData/corpora ) 
and the local path where the derivative data is to be placed.  Do not include a final "/" on these paths.

TBD: Move these two path parameters into a configuration file.  Check for final "/" and remove it if it exists.

Call the script with arguments:
corpus: a string indicating the domain, which should correspond to the source domain (e.g., ln-us-A27-molecular-biology)
start_year: the start of a range of years to process (e.g., 1997)
end_year: the end of a range of years to process (e.g., 2007)  If only one year, this should be the same as start_year.

The data for this range of years must exist in the source corpus directories.

e.g. sh run_term_features.sh ln-us-A27-molecular-biology 2002 2002

As a result of running this script, the <corpus>/data/term_features/<year> directory will be populated for each year
in the range.  Each output file corresponds to an input document and 
contains lines of the form: <term> <feature> <freq>  
When the feature is null, the freq is the count of all occurrences of the term in the document.
Rough time estimate is 1 minute to process 1000 files.

Additionally, several files will be added to the <corpus>/data/tv directory for each year in the range: 
<year>.tf   
<term> <feature> <doc_freq> <prob>
e.g., heterologous sequence   prev_V=flanks   5       0.000136

<year>.terms
<term> <doc_freq> <term_freq> <prob>
e.g., paraffin-embedded material      2       3       0.000055

<year>.feats
<feature> <doc_freq> <feature_freq> <prob>
e.g., prev_VNP=requires|changes|in    5       7       0.000136

<year>.cs

At this point, depending on the number of years processed for the corpus, you can do ACT role analysis for 
specific years or do temporal feature analysis for a range of years.

Temporal feature analysis (incomplete)

Next run 
sh make_tf_f.sh <corpus>

TBD: add a year_list parameter to make_tf_f.sh so that the years can be passed in
rather than hard coded.

This creates the <year>.tf.f file

<year>.tf.f

run fan.py (feature analysis)

///

ACT Role detection

go to roles code directory
python
import role
role.run_tf_steps("ln-us-cs-500k", 2002, 2002, "act", ["tc", "tcs", "fc", "uc", "prob"])  

This creates:
-rw-r--r-- 1 anick grad   4720633 Jul  5 20:37 2002.act.tfc
-rw-r--r-- 1 anick grad   3128299 Jul  5 20:37 2002.act.tc
-rw-r--r-- 1 anick grad   1212780 Jul  5 20:38 2002.act.tcs
-rw-r--r-- 1 anick grad  26936288 Jul  5 20:46 2002.act.fc
-rw-r--r-- 1 anick grad   7830750 Jul  5 20:46 2002.act.fc_uc
-rw-r--r-- 1 anick grad        51 Jul  5 20:46 2002.act.cat_prob
-rw-r--r-- 1 anick grad   1698193 Jul  5 20:52 2002.act.fc_kl
-rw-r--r-- 1 anick grad  36605657 Jul  5 20:52 2002.act.fc_prob

Now run nbayes.py:
python
import nbayes
# (3) nbayes.run_steps("ln-us-A27-molecular-biology", 2002, ["nb", "ds", "cf"])

This creates
-rw-r--r-- 1 anick grad  49842024 Aug 19 23:18 2002.act.cat.w0.1
-rw-r--r-- 1 anick grad 114735337 Aug 19 23:25 2002.act.cat.w0.05
-rw-r--r-- 1 anick grad 199688870 Aug 19 23:35 2002.act.cat.w0.0
-rw-r--r-- 1 anick grad  79026260 Aug 19 23:52 2002.ds
-rw-r--r-- 1 anick grad   2965726 Aug 19 23:53 2002.act.cat.w0.0_r10-100000_ds1.5
-rw-r--r-- 1 anick grad   2767188 Aug 19 23:55 2002.act.cat.w0.0_r2-10_ds1.5

# (4) nbayes.run_filter_tf_file("ln-us-A27-molecular-biology", 2002, "0.0") # create a.tf, needed for running polarity
This creates
-rw-r--r-- 1 anick grad   1170916 Aug 20 11:48 2002.t.tf
-rw-r--r-- 1 anick grad  40564925 Aug 20 11:48 2002.a.tf

# (5) role.run_tf_steps("ln-us-A27-molecular-biology", 2002, 2002, "pn", ["tc", "tcs", "fc", "uc", "prob"], "a")
This creates
-rw-r--r-- 1 anick grad    825837 Aug 20 12:38 2002.a.pn.tfc
-rw-r--r-- 1 anick grad    497047 Aug 20 12:38 2002.a.pn.tc
-rw-r--r-- 1 anick grad    168944 Aug 20 12:38 2002.a.pn.tcs
-rw-r--r-- 1 anick grad   1895790 Aug 20 12:39 2002.a.pn.fc
-rw-r--r-- 1 anick grad    756733 Aug 20 12:39 2002.a.pn.fc_uc
-rw-r--r-- 1 anick grad        33 Aug 20 12:39 2002.a.pn.cat_prob
-rw-r--r-- 1 anick grad    120284 Aug 20 12:40 2002.a.pn.fc_kl
-rw-r--r-- 1 anick grad   2273975 Aug 20 12:40 2002.a.pn.fc_prob

# (6) nbayes.run_steps("ln-us-A27-molecular-biology", 2002, ["nb", "ds", "cf"], cat_type="pn", subset="a") 
This creates
-rw-r--r-- 1 anick grad   5895682 Aug 20 13:01 2002.a.pn.cat.w0.1
-rw-r--r-- 1 anick grad   8966426 Aug 20 13:02 2002.a.pn.cat.w0.05
-rw-r--r-- 1 anick grad  18698897 Aug 20 13:04 2002.a.pn.cat.w0.0
-rw-r--r-- 1 anick grad  79026260 Aug 20 13:24 2002.ds
-rw-r--r-- 1 anick grad    345169 Aug 20 13:25 2002.a.pn.cat.w0.0_r10-100000_ds1.5
-rw-r--r-- 1 anick grad    357121 Aug 20 13:25 2002.a.pn.cat.w0.0_r2-10_ds1.5


TBD: make corpus_root a config parameter in nbayes.py

