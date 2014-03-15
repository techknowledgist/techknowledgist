annot.ts10.nc.lo.pa.20130415.lab
	The most recent annotation for the evaluation set of ten documents, using labels
	'y', 'n' and '?'. This file is a newer version of phr_occ.eval.lab, which is
	different in three ways: it is based on nine files, it has no '?' label, and it is
	done with an older chunker which produced more chunks.
	Files used:
	      2004/US6776488B2.xml
	      2007/US20070073479A1.xml
	      2003/US20030033114A1.xml
	      1996/US5559162A.xml
	      2011/US7916138B2.xml
	      1991/US5040845A.xml
	      2007/US20070054120A1.xml
	      2003/US20030058429A1.xml
	      2003/US20030142429A1.xml
	      2003/US20030114919A1.xml

annot.ts10.nc.lo.mv.20130424.lab
	Has labels for a subset of annot.ts10.nc.lo.pa.20130415.lab. See notes in
	notes-mv.txt. Used for inter-annotator agreement, to be measured with the script
	in ../../iaa.py.

ontology-evaluation-20121128.lab
ontology-evaluation-20121128.txt
	Used to get precision numbers on the first ontology produced for maturity
	calculation.

phr_occ.eval.unlab
	File intended for annotating all term-document pairs in nine files. Not used due
	to time constraints.

phr_occ.eval.lab
	This was used instead. Earlier version of annot.ts10.nc.lo.pa.20130415.lab.


compare-labeled-sets.py

doc_feats.eval

phr_occ.lab
phr_occ.uct
phr_occ.cum
	The first is the annotation file for training data derived from the
	sample-500 data set, the terms are ordered on frequency. The second has
	frequencies for each term and the third cumulative counts.

phr_occ.20130218.relab
	Not sure what this is, but it has the "?" label added. It has 2682 lines
	and may or may not overlap with phr_occ.lab (I did not check this, but
	some frequent terms like "data" and "image" are not in this file.

gold-training.txt
gold-testing.txt
	Derived from phr_occ.lab and phr_occ.eval.lab as follows:
	$ egrep "^(y|n)" phr_occ.lab > gold-training.txt
	$ egrep "^(y|n)" phr_occ.eval.lab > gold-testing.txt
