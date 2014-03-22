== cat annotation (components, attributes, tasks)

This if for the health corpus only. Need to add the cs corpus.

There are filter files in: 

	lists/cs_eval_actux_2002.act.cat.w0.0_r10-100000_ds1.5.1000
	lists/cs_eval_pnux_2002.a.pn.cat.w0.0_r10-100000_ds1.5.1000
	lists/health_eval_actux_2002.act.cat.w0.0_r10-100000_ds0.05.1000
	lists/health_eval_pnux_2002.a.pn.cat.w0.0_r10-100000_ds0.05.1000



1. creating the annotation file using the term filter

# health corpus
setenv CORPUS /home/j/corpuswork/fuse/FUSEData/corpora/ln-us-14-health/subcorpora/2002
setenv ANNOTATION $CORPUS/data/t0_annotate/technologies/first-100/annotate.terms.context.txt
python filter.py $ANNOTATION health.2002.act.context.txt lists/health_eval_actux_2002.act.cat.w0.0_r10-100000_ds0.05.1000

python filter.py $ANNOTATION health.2002.pn.context.txt lists/health_eval_pnux_2002.a.pn.cat.w0.0_r10-100000_ds0.05.1000


# cs corpus
setenv CORPUS /home/j/corpuswork/fuse/FUSEData/corpora/ln-us-cs-500k/subcorpora/2002
setenv ANNOTATION $CORPUS/data/t0_annotate/technologies/first-100/annotate.terms.context.txt
python filter.py $ANNOTATION cs.2002.act.context.txt lists/cs_eval_actux_2002.act.cat.w0.0_r10-100000_ds1.5.1000

python filter.py $ANNOTATION cs.2002.pn.context.txt lists/cs_eval_pnux_2002.a.pn.cat.w0.0_r10-100000_ds1.5.1000


2. Splitting the annotation file

# health
python split_annotation_file.py 100 health.2002.act.context.txt
mv health.2002.act.context.txt.1 health.2002.act.1.pa.context.txt
mv health.2002.act.context.txt.2 health.2002.act.2.mv.context.txt
mv health.2002.act.context.txt.3 health.2002.act.3.jp.context.txt
python split_annotation_file.py 81 health.2002.pn.context.txt
mv health.2002.pn.context.txt.1 health.2002.pn.1.pa.context.txt
mv health.2002.pn.context.txt.2 health.2002.pn.2.mv.context.txt
mv health.2002.pn.context.txt.3 health.2002.pn.3.jp.context.txt

# cs
python split_annotation_file.py 100 cs.2002.act.context.txt
mv cs.2002.act.context.txt.1 cs.2002.act.1.pa.context.txt
mv cs.2002.act.context.txt.2 cs.2002.act.2.mv.context.txt
mv cs.2002.act.context.txt.3 cs.2002.act.3.jp.context.txt
python split_annotation_file.py 42 cs.2002.pn.context.txt
mv cs.2002.pn.context.txt.1 cs.2002.pn.1.pa.context.txt
mv cs.2002.pn.context.txt.2 cs.2002.pn.2.mv.context.txt
mv cs.2002.pn.context.txt.3 cs.2002.pn.3.jp.context.txt

