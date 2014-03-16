== cat annotation (components, attributes, tasks)

health.2002.100.frequent.1000.context.txt
health.2002.100.rare.1000.context.txt


1. creating the annotaiton file using the term filter

setenv DIR /home/j/corpuswork/fuse/FUSEData/corpora/ln-us-14-health/subcorpora/2002/data/t0_annotate/technologies/first-100

python filter.py $DIR/annotate.terms.context.txt health.2002.100.frequent.1000.context.txt lists/health.2002.act.cat.w0.0_gt10_100000_ds1.5_shuf_1000 

python filter.py $DIR/annotate.terms.context.txt health.2002.100.rare.1000.context.txt lists/health.2002.act.cat.w0.0_gt2_10_ds1.5_shuf_1000 


2. Splitting the annotation file

python split_annotation_file.py 100 health.2002.100.frequent.1000.context.txt
mv health.2002.100.frequent.1000.context.txt.1 health.2002.100.frequent.1000.1.jp.context.txt
mv health.2002.100.frequent.1000.context.txt.2 health.2002.100.frequent.1000.2.pa.context.txt
mv health.2002.100.frequent.1000.context.txt.3 health.2002.100.frequent.1000.3.mv.context.txt
mv health.2002.100.frequent.1000.context.txt.4 health.2002.100.frequent.1000.4.xx.context.txt
