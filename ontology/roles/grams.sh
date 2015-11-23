# grams.sh

# call from the local directory:
# /home/j/anick/patent-classifier/ontology/roles/grams.sh 

# Depends upon having the output of these runs in the current directory:
# es_np_query.dump_ngrams("i_bio_2003", 3, "/home/j/anick/patent-classifier/ontology/roles/data/nc/bio_2003/trigrams.inst.filt")
# es_np_query.dump_ngrams("i_bio_2003", 2, "/home/j/anick/patent-classifier/ontology/roles/data/nc/bio_2003/bigrams.inst.filt")  

# Massage files to produce statstics

# term doc_id
#cat trigrams.inst.filt | cut -f1,3 | sort | uniq > trigrams.inst.filt.su
cat bigrams.inst.filt | cut -f1,3 | sort | uniq > bigrams.inst.filt.su

# doc_freq term
#cat trigrams.inst.filt.su | cut -f1 | sort | uniq -c | sort -nr | python /home/j/anick/patent-classifier/ontology/creation/reformat_uc1.py | sort -nr > trigrams.inst.filt.su.f1.uc1.nr
cat bigrams.inst.filt.su | cut -f1 | sort | uniq -c | sort -nr | python /home/j/anick/patent-classifier/ontology/creation/reformat_uc1.py | sort -nr > bigrams.inst.filt.su.f1.uc1.nr

# term pos
#cat trigrams.inst.filt | cut -f1,4 | sort | uniq > trigrams.pos
cat bigrams.inst.filt | cut -f1,4 | sort | uniq > bigrams.pos

# number of documents containing a trigram
#cat trigrams.inst.filt.su | cut -f2 | sort | uniq > trigrams.doc_id

echo "[grams.sh]Completed bigram/trigram files.  Next step: Run es_np_nc.trigram2info in python"
