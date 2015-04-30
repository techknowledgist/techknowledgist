elasticsearch config files are here: /indexes/elasticsearch/config


cd /home/j/anick/patent-classifier/ontology/roles

# to test if es is running

To test if es is up and running:

curl localhost:9200

on sarpedon, we get:

[anick@sarpedon roles]$ curl localhost:9200
{
  "status" : 200,
  "name" : "Scarlet Spider",
  "cluster_name" : "elasticsearch",
  "version" : {
    "number" : "1.4.1",
    "build_hash" : "89d3241d670db65f994242c8e8383b169779e2d4",
    "build_timestamp" : "2014-11-26T15:49:29Z",
    "build_snapshot" : false,
    "lucene_version" : "4.10.2"
  },
  "tagline" : "You Know, for Search"
}

To get size of database
curl -XGET localhost:9200/i_testg/_count?pretty=true&q={'matchAll':{''}}   


#To print out info for a single doc

python2.7
import es_np_nc
d = es_np_nc.test_docNc("US20070082860A1")
d.print_pinfo_len(None, 3, True)

#To find doc_ids which contain a phrase                                                                                                         
es_np_query.docs_matching("human cell line")    

# To get phrase info from a subcorpus already output as ba_vectors
fields are term, tf, loc1, 0, 1, 2, (0,1), (1,2), (0,3)
ba_vectors.hcl.txt

cat ba_vectors.hcl.txt | cut -f1,9 | more  => ac
cat ba_vectors.hcl.txt | cut -f1,8 | egrep '    b'| more  => bc before

unique counts by phrase types
-rw-r--r-- 1 anick grad   1773444 Mar 15 22:34 ba_vectors.hcl.txt
-rw-r--r-- 1 anick grad      7220 Mar 15 22:39 ba_vectors.hcl.uc
-rw-r--r-- 1 anick grad       108 Mar 15 22:40 ba_vectors.hcl.ab_bc.uc
-rw-r--r-- 1 anick grad        30 Mar 15 22:43 ba_vectors.hcl.ab.uc
-rw-r--r-- 1 anick grad        30 Mar 15 22:43 ba_vectors.hcl.bc.uc
-rw-r--r-- 1 anick grad        30 Mar 15 22:52 ba_vectors.hcl.a.uc
-rw-r--r-- 1 anick grad        30 Mar 15 22:52 ba_vectors.hcl.b.uc
-rw-r--r-- 1 anick grad        30 Mar 15 22:52 ba_vectors.hcl.c.uc
-rw-r--r-- 1 anick grad     50578 Mar 16 11:26 es_np_nc.py
-rw-r--r-- 1 anick grad     24715 Mar 16 11:26 es_np_nc.pyc
-rw-r--r-- 1 anick grad        30 Mar 16 11:32 ba_vectors.hcl.ac.uc

To create annotation files

python2.7
import es_np_nc
import es_np_query
# Get a set of doc_ids
ds = es_np_query.docs_matching("cell")
# create annotation and corresponding doc_id files (so we know which articles the phrases come from)
# naming convention for output_file_prefix: use query term and doc_id_list range (for 1st ten docs, range is 0-10) 
es_np_nc.print_annotation_file(ds[0:10], l_phr_length=[3], output_file_prefix="cell_0-10") 
es_np_nc.print_annotation_file(ds[10:30], l_phr_length=[3], output_file_prefix="cell_10-30") 

labels should be inserted as the first column in each line:
l(eft bracketed)
r(ight bracketed)
b(i-branching)
n(ame)  e.g.,  | gonzalgo m l | 
e(rroneous phrase)   e.g.,  | role ofenvironntal factors | 
?(don't know)

Comments can be added at the end of the line

To look at data for a single doc:

python2.7
import es_np_nc
import es_np_query
# to get ids of docs:
d = es_np_query.docs_matching("human cell line")
# to get info for a given doc
dnc = es_np_nc.docNc("US7189536B2")
dnc.print_pinfo_len(None, phr_len=3, verbose_p=True)

fields:
fp: phrase, tf, loc1
ba: (0), (1), (2), (0,1), (1,2), (0,2)
pp: (0, "l"), (0, "r"), (1, "l"), (1, "r"), (2, "l"), (2, "r")

fields:
phrase, term_freq, first_sentence_location, w1 relative location, w2 rl, w3 rl, bigram AB rl, BC rl, AC rl.
(term_freq is the number of occurrences of the phrase in the document.)

more ba_vectors.hcl.txt
amino acid sequences    75      6       n       n       b       a       n       n
signal transduction cascades    1       17      a       a       n       a       n       n
cell cycle progression  1       18      b       n       a       a       n       n


##############################################################
corpus statistics for biomed patents year 2003

/home/j/anick/patent-classifier/ontology/roles/data/patents/ln-us-A27-molecular-biology/data/term_features/2003
[anick@sarpedon 2003]$ ls -1 | wc -l
38343

# Search ES for all instances of a 3 word phrase.  Return a list of [phr doc_id] pairs
res = es_np_query.qmamf_long(l_query_must=[["length", 3]],l_fields=["doc_id", "phr"])  ///

# Using the result r, write out the phrase and doc_id data for length 3 instances to bio.2003.3.inst
es_np_query.dump_rfields(res, l_fieldnames=["phr", "doc_id"], l_fieldtypes=["s", "s"], output_file="bio.2003.3.inst")
(Note this file has been overwritten!)

# apply the illegal phrase filter to the length 3 instances
# to produce bio.2003.3.inst.filt
es_np_nc.filter_phr_doc_file("bio.2003.3.inst") 

# Do more filtering to remove illegal punc(,+) and phrases starting with non alpha(a-z) characters.
# This removes ~ 50k instances
# Note: we should also filter for phrase character length
# and remove phrases that contain a word with non alphnumeric chars (a1 ≅ a2)
cat bio.2003.3.inst.filt | egrep '^[a-z]' | egrep -v '[,\+]' > bio.2003.3.inst.filt2

[anick@sarpedon roles]$ wc -l bio.2003.3.inst.filt2
2126633 bio.2003.3.inst.filt2

# sort uniq to get document frequencies rather than collection frequencies
sort bio.2003.3.inst.filt2 | uniq > bio.2003.3.inst.filt2.su

[anick@sarpedon roles]$ wc -l bio.2003.3.inst.filt2.su
1320668 bio.2003.3.inst.filt2.su

# get doc freq of each phrase, sort by number reverse
cat bio.2003.3.inst.filt2.su | cut -f1 | sortuc1 | sortnr > bio.2003.3.inst.filt2.su.f1.uc1.nr

# How many triples only occur in one doc?
[anick@sarpedon roles]$ cat bio.2003.3.inst.filt2.su.f1.uc1.nr | egrep '^1      ' | wc -l
333565

# Now do the same for bigram phrases
r = es_np_query.qmamf_long(l_query_must=[["length", 2]],l_fields=["doc_id", "phr"], size=1000)
>>> len(r)
9812508

es_np_query.dump_rfields(r, l_fieldnames=["phr", "doc_id"], l_fieldtypes=["s", "s"], output_file="bio.2003.2.inst")

# Do the filtering of illegal phrases (all folded into a single function now)
>>> es_np_nc.filter_phr_doc_file("bio.2003.2.inst")

# sort uniq to get document frequencies rather than collection frequencies
sort bio.2003.2.inst.filt | uniq > bio.2003.2.inst.filt.su

# unique bigram doc_id pairs
[anick@sarpedon roles]$ wc -l bio.2003.2.inst.filt.su
5052994 bio.2003.2.inst.filt.su

# get doc freq of each phrase, sort by number reverse
cat bio.2003.2.inst.filt.su | cut -f1 | sortuc1 | sortnr > bio.2003.2.inst.filt.su.f1.uc1.nr

# number of unique bigrams for the year 2003
[anick@sarpedon roles]$ wc -l bio.2003.2.inst.filt.su.f1.uc1.nr
912549 bio.2003.2.inst.filt.su.f1.uc1.nr

# How many bigrams only occur in one doc?
[anick@sarpedon roles]$ cat bio.2003.2.inst.filt.su.f1.uc1.nr | egrep '^1      ' | wc -l
511866

####################################
# Redoing stats using canonicalized phrases
# after canonicalizing the phrases in bio.2003.3.inst.filt2
>>> es_np_nc.can_phr_doc_file("bio.2003.3.inst.filt2")  

# canonical trigrams
[anick@sarpedon roles]$ wc -l bio.2003.3.inst.filt2.c
2126633 bio.2003.3.inst.filt2.c
[anick@sarpedon roles]$ wc -l bio.2003.3.inst.filt2.c2s
469168 bio.2003.3.inst.filt2.c2s

# sort uniq to get document frequencies rather than collection frequencies
# note we remove the (filt)2 at this point
sort bio.2003.3.inst.filt2.c | uniq > bio.2003.3.inst.filt.c.su

[anick@sarpedon roles]$ wc -l bio.2003.3.inst.filt.c.su

# get doc freq of each phrase, sort by number reverse
cat bio.2003.3.inst.filt.c.su | cut -f1 | sortuc1 | sortnr > bio.2003.3.inst.filt.c.su.f1.uc1.nr

# surface trigrams count
[anick@sarpedon roles]$ cat bio.2003.3.inst.filt.su.f1.uc1.nr | wc -l
504203
# canonical trigrams count
[anick@sarpedon roles]$ wc -l bio.2003.3.inst.filt.c.su.f1.uc1.nr
469153 bio.2003.3.inst.filt.c.su.f1.uc1.nr

# How many triples only occur in one doc?
[anick@sarpedon roles]$ cat bio.2003.3.inst.filt.su.f1.uc1.nr | egrep '^1      ' | wc -l
333565
cat bio.2003.3.inst.filt.c.su.f1.uc1.nr | egrep '^1      ' | wc -l
308148

# canonicalized bigrams

>>> es_np_nc.can_phr_doc_file("bio.2003.2.inst.filt") 

# sort uniq to get document frequencies rather than collection frequencies
sort bio.2003.2.inst.filt.c | uniq > bio.2003.2.inst.filt.c.su

# unique bigram doc_id pairs
[anick@sarpedon roles]$ wc -l bio.2003.2.inst.filt.su
5052994 bio.2003.2.inst.filt.su

[anick@sarpedon roles]$ wc -l bio.2003.2.inst.filt.c.su
4816303 bio.2003.2.inst.filt.c.su

# get doc freq of each phrase, sort by number reverse
cat bio.2003.2.inst.filt.c.su | cut -f1 | sortuc1 | sortnr > bio.2003.2.inst.filt.c.su.f1.uc1.nr

# number of unique bigrams for the year 2003
[anick@sarpedon roles]$ wc -l bio.2003.2.inst.filt.su.f1.uc1.nr
912549 bio.2003.2.inst.filt.su.f1.uc1.nr
[anick@sarpedon roles]$ wc -l bio.2003.2.inst.filt.c.su.f1.uc1.nr

[anick@sarpedon roles]$ wc -l bio.2003.2.inst.filt.c.su.f1.uc1.nr
806785 bio.2003.2.inst.filt.c.su.f1.uc1.nr

# How many bigrams only occur in one doc?
[anick@sarpedon roles]$ cat bio.2003.2.inst.filt.su.f1.uc1.nr | egrep '^1      ' | wc -l
511866
[anick@sarpedon roles]$ cat bio.2003.2.inst.filt.c.su.f1.uc1.nr | egrep '^1     ' | wc -l
449260

Corpus statistics in directory /home/j/anick/patent-classifier/ontology/roles
File: bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats

///

The fields in the output file
1. trigram, 2. trigram doc freq, 3. freq(AB), 4. freq(BC), 5. freq(AC), 6. diff(AB - BC), 7. ratio(|AB - BC)/(AB + BC), 8. bracketing, 9. Trigram prominence

All frequencies are # docs which contain the phrase within the 2003 molecular biology patents (38343 docs).
diff(AB - BC) is the raw difference in doc freq between the left and right bigrams.
Bracketing (L,R,U) is based on the sign of the raw difference.  U means no bigrams occurred on their own.
For ratios > .2 and <.8, "B" is appended to the bracketing to indicate the potential for a bi-branching 
interpretation.
Trigram prominence is T if the trigram is more frequent than either bigram, and B otherwise.  

Some useful summary views ofCorpus statistics in directory /home/j/anick/patent-classifier/ontology/roles
File: bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats

The fields in the output file
1. trigram, 2. trigram doc freq, 3. freq(AB), 4. freq(BC), 5. freq(AC), 6. diff(AB - BC), 7. ratio(|AB - BC)/(AB + BC\
), 8. bracketing, 9. Trigram prominence

All frequencies are # docs which contain the phrase within the 2003 molecular biology patents (38343 docs).
diff(AB - BC) is the raw difference in doc freq between the left and right bigrams.
Bracketing (L,R,U) is based on the sign of the raw difference.  U means no bigrams occurred on their own.
For ratios > .2 and <.8, "B" is appended to the bracketing to indicate the potential for a bi-branching
interpretation.
Trigram prominence is T if the trigram is more frequent than either bigram, and B otherwise.

Some useful summary views of the data:

Branching based on raw bigram frequencies
cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f1,3,4,8 | more

Trigrams which are more frequent than their constituent bigrams
cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f1,9 | more

Possible bi-branching phrases (based on bigram counts for AB and BC):
cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f1,3,4,7,8 | grep B | more

Sums:

[anick@sarpedon roles]$ cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f1 | wc -l
469153
[anick@sarpedon roles]$ cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f8 | grep L | wc -l 
117131
[anick@sarpedon roles]$ cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f8 | grep R | wc -l 
275440
[anick@sarpedon roles]$ cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f8 | grep U | wc -l 
76582
[anick@sarpedon roles]$ cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f8 | grep B | wc -l 
25349
[anick@sarpedon roles]$ cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f8 | grep RB | wc -l 
13368
[anick@sarpedon roles]$ cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f8 | grep LB | wc -l 
11981
[anick@sarpedon roles]$ cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f9 | grep T | wc -l 
81389
[anick@sarpedon roles]$ cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f9 | grep B | wc -l 
387764
[anick@sarpedon roles]$ cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f1,2,8 | wc -l
469153
[anick@sarpedon roles]$ cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f1,2,8 | egrep '   [0-9]   ' | wc -l
454059
[anick@sarpedon roles]$ cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f1,2,8 | egrep '   [0-9]   ' | grep U | wc -l
75763

# unknown bracketing as a function of trigram frequency
[anick@sarpedon roles]$ cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f1,2,8 | egrep '   [0-5]   ' | wc -l
440181
[anick@sarpedon roles]$ cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f1,2,8 | egrep '   [0-5]   ' | grep U| wc -l
74667
[anick@sarpedon roles]$ cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f1,2,8 | egrep '   [0-3]   ' | wc -l418683
[anick@sarpedon roles]$ cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f1,2,8 | egrep '   [0-3]   ' | grep U | wc -l
72644
[anick@sarpedon roles]$ cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f1,2,8 | egrep '   [0-2]   ' | grep U | wc -l
69891
[anick@sarpedon roles]$ cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f1,2,8 | egrep '   [0-2]   ' | wc -l393661
[anick@sarpedon roles]$ cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f1,2,8 | egrep '   [1]     ' | wc -l
308148
[anick@sarpedon roles]$ cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f1,2,8 | egrep '   [1]     ' | grep U | wc -l
57175

[anick@sarpedon roles]$ cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f1,2,8 | egrep '   [1]     ' | grep U | more

# documents: 		 38343
Total trigrams:		469153
left branching:		117131
right branching: 	275440
unknown: 		 76582
Bi-Branching: 		 25349
Rbi-branching: 		 13368
Lbi-branching: 		 11981
Trigram dominant: 	 81389
Bigram dominant: 	387764
Frequency 1 trigrams:   308148
Frequency 1 unknown:     57175

# documents: 		 38343
Total trigrams:		469153
cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f1,8 | grep L | more
left branching:		117131
cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f1,8 | grep R | more
right branching: 	275440
cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f1,8 | grep U | more
unknown: 		 76582
cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f1,8 | grep B | more
Bi-Branching: 		 25349
cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f1,8 | grep RB | more
Rbi-branching: 		 13368
 cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f1,8 | grep LB | more
Lbi-branching: 		 11981
cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f1,9 | grep T | more
Trigram dominant: 	 81389
cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f1,9 | grep B | more
Bigram dominant: 	387764
cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f1,2,8 | egrep '   [0-9]   ' | more
Frequency 1 trigrams:   308148
cat bio.2003.3.inst.filt.c.su.f1.uc1.nr.stats | cut -f1,2,8 | egrep '   [0-9]   ' | grep U | more
Frequency 1 unknown:     57175

##########################################
Diagnosing why "amino acid sequences" has so many loc1 and freq similaries in ba file
ba_vectors.hcl.txt

Rewrote code to output doc_id.
es_np_nc.dump_phr_vectors("human cell line", "ba_vectors.hcl_test10.txt", 10)

Need to look at phr_feats files to check on term locations
cd /home/j/corpuswork/fuse/FUSEData/corpora/ln-us-A27-molecular-biology/subcorpora/2003/config
[anick@sarpedon config]$ ls
files.txt  general.txt  pipeline-default.txt

[anick@sarpedon config]$ cat files.txt | grep US20040033583A1 
2003    /home/j/corpuswork/fuse/FUSEData/2013-04/ln_uspto/2004/024/US20040033583A1.xml  2004/024/US20040033583A1.xml

cd /home/j/corpuswork/fuse/FUSEData/corpora/ln-us-A27-molecular-biology/subcorpora/2003/data/d3_phr_feats/01/files
gunzip -c 2004/024/US20040033583A1.xml.gz | more

cat /home/j/corpuswork/fuse/FUSEData/corpora/ln-us-A27-molecular-biology/subcorpora/2003/config/files.txt | grep 

########################################
Debugging es indexing error.

error trying to populate i_bio

[es_np_index.py] Bulk loaded sublist 146
[es_np_index.py] Bulk loaded sublist 147
WARNING:elasticsearch:POST http://localhost:9200/_bulk [status:N/A request:10.443s]
Traceback (most recent call last):
  File "/usr/lib/python2.7/site-packages/elasticsearch/connection/http_urllib3.py", line 46, in perform_request
    response = self.pool.urlopen(method, url, body, **kw)
  File "/usr/lib/python2.7/site-packages/urllib3/connectionpool.py", line 541, in urlopen
    body=body, headers=headers)
  File "/usr/lib/python2.7/site-packages/urllib3/connectionpool.py", line 398, in _make_request
    self, url, "Read timed out. (read timeout=%s)" % read_timeout)
ReadTimeoutError: HTTPConnectionPool(host='localhost', port=9200): Read timed out. (read timeout=10)
WARNING:elasticsearch:Connection <Urllib3HttpConnection: http://localhost:9200> has failed for 1 times in a row, putting on 60 second timeout.
WARNING:urllib3.connectionpool:Retrying (3 attempts remain) after connection broken by 'CannotSendRequest()': /_bulk
WARNING:elasticsearch:POST http://localhost:9200/_bulk [status:N/A request:25.948s]
Traceback (most recent call last):

In log: 

[anick@sarpedon mapper]$ cd /indexes/elasticsearch/logs
...
-rw-r--r-- 1 anick grad     85070 Mar 29 22:12 elasticsearch.log.2015-03-29
-rw-r--r-- 1 anick grad    651455 Mar 30 23:48 elasticsearch.log.2015-03-30
-rw-r--r-- 1 anick grad 100025000 Mar 31 11:10 elasticsearch.log
[anick@sarpedon logs]$ more elasticsearch.log
[2015-03-31 00:09:40,350][WARN ][monitor.jvm              ] [Terrax the Tamer] [gc][young][4187255][30363] duration [4.8s], collections [1]/[6
.1s], total [4.8s]/[6.5m], memory [843.5mb]->[499.8mb]/[989.8mb], all_pools {[young] [219.3mb]->[1mb]/[273mb]}{[survivor] [34.1mb]->[0b]/[34.1
mb]}{[old] [590mb]->[499.1mb]/[682.6mb]}
[2015-03-31 00:18:32,154][WARN ][http.netty               ] [Terrax the Tamer] Caught exception while handling client http traffic, closing co
nnection [id: 0x3e63e080, /127.0.0.1:53100 => /127.0.0.1:9200]
java.lang.OutOfMemoryError: Java heap space
[2015-03-31 00:27:19,456][DEBUG][action.bulk              ] [Terrax the Tamer] [i_bio][2], node[b52PpygYSIS138OHonpgXg], [P], s[STARTED]: Fail
ed to execute [org.elasticsearch.action.bulk.BulkShardRequest@3240547c]
java.lang.OutOfMemoryError: Java heap space
[2015-03-31 00:27:19,726][WARN ][index.merge.scheduler    ] [Terrax the Tamer] [i_bio][4] failed to merge
org.apache.lucene.store.AlreadyClosedException: refusing to delete any files: this IndexWriter hit an unrecoverable exception
        at org.apache.lucene.index.IndexFileDeleter.ensureOpen(IndexFileDeleter.java:354)
        at org.apache.lucene.index.IndexFileDeleter.deleteFile(IndexFileDeleter.java:719)
        at org.apache.lucene.index.IndexFileDeleter.refresh(IndexFileDeleter.java:451)
        at org.apache.lucene.index.IndexWriter.merge(IndexWriter.java:3783)
        at org.apache.lucene.index.ConcurrentMergeScheduler.doMerge(ConcurrentMergeScheduler.java:405)
        at org.apache.lucene.index.TrackingConcurrentMergeScheduler.doMerge(TrackingConcurrentMergeScheduler.java:106)
        at org.apache.lucene.index.ConcurrentMergeScheduler$MergeThread.run(ConcurrentMergeScheduler.java:482)
Caused by: java.lang.OutOfMemoryError: Java heap space
[2015-03-31 00:27:19,747][WARN ][index.engine.internal    ] [Terrax the Tamer] [i_bio][4] failed engine [merge exception]
org.apache.lucene.index.MergePolicy$MergeException: org.apache.lucene.store.AlreadyClosedException: refusing to delete any files: this IndexWr
iter hit an unrecoverable exception
        at org.elasticsearch.index.merge.scheduler.ConcurrentMergeSchedulerProvider$CustomConcurrentMergeScheduler.handleMergeException(Concur
rentMergeSchedulerProvider.java:133)
        at org.apache.lucene.index.ConcurrentMergeScheduler$MergeThread.run(ConcurrentMergeScheduler.java:518)
Caused by: org.apache.lucene.store.AlreadyClosedException: refusing to delete any files: this IndexWriter hit an unrecoverable exception
        at org.apache.lucene.index.IndexFileDeleter.ensureOpen(IndexFileDeleter.java:354)
        at org.apache.lucene.index.IndexFileDeleter.deleteFile(IndexFileDeleter.java:719)
        at org.apache.lucene.index.IndexFileDeleter.refresh(IndexFileDeleter.java:451)
        at org.apache.lucene.index.IndexWriter.merge(IndexWriter.java:3783)
        at org.apache.lucene.index.ConcurrentMergeScheduler.doMerge(ConcurrentMergeScheduler.java:405)
        at org.apache.lucene.index.TrackingConcurrentMergeScheduler.doMerge(TrackingConcurrentMergeScheduler.java:106)
        at org.apache.lucene.index.ConcurrentMergeScheduler$MergeThread.run(ConcurrentMergeScheduler.java:482)
Caused by: java.lang.OutOfMemoryError: Java heap space
[2015-03-31 00:27:19,771][DEBUG][action.bulk              ] [Terrax the Tamer] [i_bio][0] failed to execute bulk item (index) index {[i_bio][s
ent][US20030211131A1_367], source[{"loc": 367, "domain": "biology", "sterms": ["fermentor_medium", "liter", "glucose", "g", "yeast_extract", "
g", "soy_peptone", "g", "nh4", "hpo4", "g", "k2hpo4_.3_h2o", "g", "kh2po4", "g", "mgso4", "g", "feso4_.7_h2o", "mg", "coso4_.7_h2o", "mg", "zn
so4_.7_h2o", "mg", "mncl2_.4_h2o", "mg", "cacl2_.2_h2o", "mg", "cucl2_.2_h2o", "mg", "thiamine_hydrochloride", "mg", "mazu_df-204", "breox_fmt
-30_antifoam", "ml", "kanamycin_sulfate", "mg", "tetracycline_hydrochloride", "mg"], "section": "DESC", "sheads": ["medium", "liter", "glucose
", "g", "extract", "g", "peptone", "g", "nh4", "hpo4", "g", "h2o", "g", "kh2po4", "g", "mgso4", "g", "h2o", "mg", "h2o", "mg", "h2o", "mg", "h
2o", "mg", "h2o", "mg", "h2o", "mg", "hydrochloride", "mg", "df-204", "antifoam", "ml", "sulfate", "mg", "hydrochloride", "mg"], "year": 2003,
 "doc_id": "US20030211131A1"}]}
org.elasticsearch.index.engine.IndexFailedEngineException: [i_bio][0] Index failed for [sent#pport.replication.TransportShardReplicationOperationAction$AsyncShardOperationAction.performOnPrimary(Tr
ansportShardReplicationOperationAction.java:511)
        at org.elasticsearch.action.support.replication.TransportShardReplicationOperationAction$AsyncShardOperationAction$1.run(TransportShar
dReplicationOperationAction.java:419)
        at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1145)
        at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:615)
        at java.lang.Thread.run(Thread.java:744)
Caused by: org.apache.lucene.store.AlreadyClosedException: this IndexWriter is closed
        at org.apache.lucene.index.IndexWriter.ensureOpen(IndexWriter.java:698)
        at org.apache.earch.index.engine.internal.InternalEngine.index(InternalEngine.java:498)
        ... 8 more
Caused by: java.lang.OutOfMemoryError: Java heap space

[2015-03-31 00:27:19,884][DEBUG][action.bulk              ] [Terrax the Tamer] [i_bio][1] failed to execute bulk item (index) index {[i_bio][s
ent][US20030211632A1_74], source[{"loc": 74, "domain": "biology", "sterms": ["accordance", "invention", "non-contact_method", "small_amount", 
"source_fluid", "target"], "section": "DESC", "sheads": ["accordance", "invention", "method", "amount", "fluid", "target"], "year": 2003, "doc
_id": "US20030211632A1"}]}
org.elasticsearch.index.engine.IndexFailedEngineException: [i_bio][1] Index failed for [sent#US20030211632A1_74]
        at org.elasticsearch.index.engine.internal.InternalEngine.index(InternalEngine.java:505)
        at org.elasticsearch.index.shard.service.InternalIndexShard.index(InternalIndexShard.java:425)
        at org.elasticsearch.action.bulk.TransportShardBulkAction.shardIndexOperation(TransportShardBulkAction.java:439)
        at org.elasticsearch.action.bulk.TransportShardBulkAction.shardOperationOnPrimary(TransportShardBulkAction.java:150)
        at org.elasticsearch.action.support.replication.TransportShardReplicationOperationAction$AsyncShardOperationAction.performOnPrimary(Tr
ansportShardReplicationOperationAction.java:511)
        at org.elasticsearch.action.support.replication.TransportShardReplicationOperationAction$AsyncShardOperationAction$1.run(TransportShar
dReplicationOperationAction.java:419)
        at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1145)
        at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:615)
        at java.lang.Thread.run(Thread.java:744)
Caused by: org.apache.lucene.store.AlreadyClosedException: this IndexWriter is closed
        at org.apache.lucene.index.IndexWriter.ensureOpen(IndexWriter.java:698)
        at org.apache.lucene.index.IndexWriter.ensureOpen(IndexWriter.java:712)
        at org.apache.lucene.index.IndexWriter.updateDocument(IndexWriter.java:1507)
        at org.elasticsearch.index.engine.internal.InternalEngine.innerIndex(InternalEngine.java:578)
        at org.elasticsearch.index.engine.internal.InternalEngine.index(InternalEngine.java:498)
        ... 8 more
Caused by: java.lang.OutOfMemoryError: Java heap space

possible solutions
http://stackoverflow.com/questions/23418490/elasticsearch-high-number-of-index-causes-oom

TODO:
add es.indices.flush() to populate, run periodically.

restart es now that we've added the following to /indexes/elasticsearch/config/elasticsearch.yml

# additional configuration
bootstrap.mlockall: true
# bootstrap.mlockall: true prevents swapping, a costly operation
indices.fielddata.cache.size: "30%"
indices.cache.filter.size: "30%"

copy another db into i_bio so it is not missing.
(did this but still get missing msg from curl)

tried to clear cache but this failed:
[anick@sarpedon roles]$ curl -XPOST 'http://localhost:9200/i_bio/clear'

{"error":"ProcessClusterEventTimeoutException[failed to process cluster event (create-index [i_bio], cause [auto(index api)]) within 1m]","status":503}[anick@sarpedon roles]$ 

Still cannot populate a new index (or old)
>>> es_np_index.np_populate("i_test1", "biology", "ln-us-A27-molecular-biology", 2003, 2003, 50, True, True, 1000)  
[se_np_index.py]np_populate started at Wed Apr  1 21:04:07 2015

WARNING:elasticsearch:HEAD /i_test1 [status:404 request:0.001s]
^CTraceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "es_np_index.py", line 558, in np_populate ...

#flush of all indices worked:
curl -XPOST 'http://localhost:9200/_flush'
[anick@sarpedon roles]$ curl -XPOST 'http://localhost:9200/_flush'
{"_shards":{"total":100,"successful":50,"failed":0}}

setting heap size: http://www.elastic.co/guide/en/elasticsearch/guide/current/heap-sizing.html

#Either set heap size in the call to start es or set it as an environment variable
./bin/elasticsearch -Xmx10g -Xms10g   #min and max need to be set to prevent dynamic resizing.
# as env variable.  Use env command to see if it is set.
export ES_HEAP_SIZE=10g

MAX_LOCKED_MEMORY Maximum locked memory size. Set to "unlimited" if you use the bootstrap.mlockall
option in elasticsearch.yml. You must also set ES_HEAP_SIZE. 
(http://www.elastic.co/guide/en/elasticsearch/reference/1.4/setup-service.html)

shutdown:
[anick@sarpedon bin]$ curl -XPOST 'http://localhost:9200/_shutdown'
{"cluster_name":"elasticsearch","nodes":{"b52PpygYSIS138OHonpgXg":{"name":"Terrax the Tamer"}}}[anick@sarpedon bin]$ 

# restarted
[anick@sarpedon bin]$ /usr/local/bin/elasticsearch
[2015-04-01 22:18:05,665][WARN ][common.jna               ] Unable to lock JVM memory (ENOMEM). This can result in part of the JVM being swapped out. Increase RLIMIT_MEMLOCK (ulimit).
[2015-04-01 22:18:05,722][INFO ][node                     ] [Unseen] version[1.4.1], pid[11364], build[89d3241/2014-11-26T15:49:29Z]
[2015-04-01 22:18:05,722][INFO ][node                     ] [Unseen] initializing ...
[2015-04-01 22:18:05,725][INFO ][plugins                  ] [Unseen] loaded [], sites []
[2015-04-01 22:18:07,563][INFO ][node                     ] [Unseen] initialized
[2015-04-01 22:18:07,564][INFO ][node                     ] [Unseen] starting ...
[2015-04-01 22:18:07,674][INFO ][transport                ] [Unseen] bound_address {inet[/0:0:0:0:0:0:0:0:9302]}, publish_address {inet[/129.64.3.220:9302]}
[2015-04-01 22:18:07,691][INFO ][discovery                ] [Unseen] elasticsearch/NmpQ8WPiR_CB2gpzMgf-Ww
[2015-04-01 22:18:11,458][INFO ][cluster.service          ] [Unseen] new_master [Unseen][NmpQ8WPiR_CB2gpzMgf-Ww][sarpedon.cs.brandeis.edu][inet[/129.64.3.220:9302]], reason: zen-disco-join (elected_as_master)
[2015-04-01 22:18:11,516][INFO ][http                     ] [Unseen] bound_address {inet[/0:0:0:0:0:0:0:0:9200]}, publish_address {inet[/129.64.3.220:9200]}
[2015-04-01 22:18:11,523][INFO ][node                     ] [Unseen] started
[2015-04-01 22:18:11,524][INFO ][gateway                  ] [Unseen] recovered [0] indices into cluster_state

To restart in background;
$ bin/elasticsearch -d

To start with heap size set
$ bin/elasticsearch -Xmx2g -Xms2g
or
$ bin/elasticsearch -d -Xmx4g -Xms4g

To prevent swapping (may need root access) [http://www.elastic.co/guide/en/elasticsearch/reference/1.4/setup-configuration.html]
The third option on Linux/Unix systems only, is to use mlockall to try to lock the process address space into RAM, preventing any Elasticsearch memory from being swapped out. This can be done, by adding this line to the config/elasticsearch.yml file:

bootstrap.mlockall: true

After starting Elasticsearch, you can see whether this setting was applied successfully by checking the value of mlockall in the output from this request:

curl http://localhost:9200/_nodes/process?pretty

If you see that mlockall is false, then it means that the the mlockall request has failed. The most probable reason is that the user running Elasticsearch doesn’t have permission to lock memory. This can be granted by running ulimit -l unlimited as root before starting Elasticsearch.

Note: I cannot do this.
[anick@sarpedon logs]$ ulimit -l unlimited 
-bash: ulimit: max locked memory: cannot modify limit: Operation not permitted

4/2/15 started es with
/indexes/elasticsearch/bin/elasticsearch -d -Xmx4g -Xms4g

[anick@sarpedon bin]$ curl http://localhost:9200/_nodes/process?pretty
{
  "cluster_name" : "elasticsearch",
  "nodes" : {
    "38f9KwtyTZ-X-Ra-gTUSGw" : {
      "name" : "John Ryker",
      "transport_address" : "inet[/129.64.3.220:9302]",
      "host" : "sarpedon.cs.brandeis.edu",
      "ip" : "129.64.3.220",
      "version" : "1.4.1",
      "build" : "89d3241",
      "http_address" : "inet[/129.64.3.220:9200]",
      "process" : {
        "refresh_interval_in_millis" : 1000,
        "id" : 25156,
        "max_file_descriptors" : 4096,
        "mlockall" : false
      }
    }
  }
}

Then in python2.7

>>> es_np_index.np_populate("i_test1", "biology", "ln-us-A27-molecular-biology", 2003, 2003, 50, True, True, 1000) 
[se_np_index.py]np_populate started at Thu Apr  2 10:22:21 2015

WARNING:elasticsearch:HEAD /i_test1 [status:404 request:0.009s]
[es_np_index.py] created np index: i_test1
[es_np_index.py] created data generator for bulk loading
[tv_filepath]file: /home/j/anick/patent-classifier/ontology/roles/data/patents/ln-us-A27-molecular-biology/data/tv/
Thu Apr  2 10:22:21 2015        0       [es_np.py gen_bulk_lists]Starting make_bulk_lists for years: 2003 2003

[tv_filepath]file: /home/j/anick/patent-classifier/ontology/roles/data/patents/ln-us-A27-molecular-biology/data/tv/
[es_np_index.py] Bulk loaded sublist 1
[es_np_index.py] Bulk loaded sublist 2
[es_np_index.py] Bulk loaded sublist 3
[es_np_index.py] Bulk loaded sublist 4
[es_np_index.py] Bulk loaded sublist 5
[es_np_index.py] Bulk loaded sublist 6
[es_np_index.py] Bulk loaded sublist 7
[es_np_index.py] Bulk loaded sublist 8
[es_np_index.py] Bulk loaded sublist 9
[es_np_index.py] Bulk loaded sublist 10
[es_np_index.py] Bulk loaded sublist 11
[es_np_index.py] Bulk loaded sublist 12
[es_np_index.py] Bulk loaded sublist 13
[es_np_index.py] Bulk loaded sublist 14
[es_np_index.py] Bulk loaded sublist 15
Thu Apr  2 10:22:22 2015        0       [es_np_index.py]Completed make_bulk_lists for years: 2003 2003. Number of lines: 1002

[gen_bulk_lists]1002 lines from 1 files written to index i_test1
[es_np_index.py] Bulk loaded sublist 16
[es_np_index.py] bulk loading completed
[es_np_index.py] index refreshed
[se_np_index.py]np_populate completed at Thu Apr  2 10:22:22 2015
 (elapsed time in hr:min:sec: 0:00:01.387156)

Now try to create the full bio 2003 index:
>>> es_np_index.np_populate("i_bio", "biology", "ln-us-A27-molecular-biology", 2003, 2003, 10000, True, True, 0) 
[se_np_index.py]np_populate started at Thu Apr  2 10:37:37 2015

If this fails, add a flush command to the code.  But it worked (starting with 4G heap memory)

While populate is running
$ less /proc/meminfo
MemTotal:       74232200 kB
MemFree:        20638420 kB
Buffers:          282384 kB
Cached:         47062288 kB
SwapCached:       258044 kB
Active:         23544100 kB
Inactive:       28708932 kB ...

After an hour
MemTotal:       74232200 kB
MemFree:        14928744 kB
Buffers:          347400 kB
Cached:         50942480 kB
SwapCached:       258044 kB
Active:         25520104 kB

3 hours in:
MemTotal:       74232200 kB
MemFree:         9660860 kB
Buffers:          470796 kB
Cached:         55595532 kB
SwapCached:       236424 kB
Active:         24671160 kB
Inactive:       38146108 kB

4 hours in
MemTotal:       74232200 kB
MemFree:          582252 kB
Buffers:          500296 kB
Cached:         56320768 kB
SwapCached:       225328 kB
Active:         33699068 kB
Inactive:       38111252 kB

5 hours in
MemTotal:       74232200 kB
MemFree:         1322148 kB

Log shows warnings:

[2015-04-02 12:25:06,257][WARN ][index.engine.internal    ] [Terrax the Tamer] [i_bio][1] failed to read latest segment infos on flush
java.io.FileNotFoundException: No such file [segments_2]

[anick@sarpedon logs]$ cat elasticsearch.log | grep WARN | wc -l
92

It completed (10 hours)!

[es_np_index.py] Bulk loaded sublist 14951
[es_np_index.py] Bulk loaded sublist 14952
Thu Apr  2 20:31:02 2015        0       [es_np_index.py]Completed make_bulk_lists for years: 2003 2003. Number of lines: 173635239

[gen_bulk_lists]173635239 lines from 38343 files written to index i_bio
[es_np_index.py] Bulk loaded sublist 14953
[es_np_index.py] bulk loading completed
[es_np_index.py] index refreshed
[se_np_index.py]np_populate completed at Thu Apr  2 20:31:03 2015
 (elapsed time in hr:min:sec: 9:53:25.253449)



TODO integrate /home/j/anick/patent-classifier/ontology/doc_processing/view.py api

Memory before populating cs 2005 index
MemTotal:       74232200 kB
MemFree:          778492 kB
Buffers:          591588 kB
Cached:         55395368 kB
SwapCached:       214580 kB
Active:         33300260 kB
Inactive:       38216796 kB
Active(anon):   19488708 kB
Inactive(anon):  2607904 kB...

>>> es_np_index.np_populate("i_cs_2005", "computers", "ln-us-A21-computers", 2005, 2005, 10000, True, True, 0) 
[se_np_index.py]np_populate started at Thu Apr  2 22:43:43 2015

WARNING:elasticsearch:HEAD /i_cs_2005 [status:404 request:0.002s]
[es_np_index.py] created np index: i_cs_2005
[es_np_index.py] created data generator for bulk loading
[tv_filepath]file: /home/j/anick/patent-classifier/ontology/roles/data/patents/ln-us-A21-computers/data/tv/
Thu Apr  2 22:43:43 2015        0       [es_np.py gen_bulk_lists]Starting make_bulk_lists for years: 2005 2005

[tv_filepath]file: /home/j/anick/patent-classifier/ontology/roles/data/patents/ln-us-A21-computers/data/tv/
[es_np_index.py] Bulk loaded sublist 1
[es_np_index.py] Bulk loaded sublist 2...

Completed CS 2005:

[es_np_index.py] Bulk loaded sublist 6903
Fri Apr  3 02:44:42 2015        0       [es_np_index.py]Completed make_bulk_lists for years: 2005 2005. Number of lines: 80943875

[gen_bulk_lists]80943875 lines from 37273 files written to index i_cs_2005
[es_np_index.py] Bulk loaded sublist 6904
[es_np_index.py] bulk loading completed
[es_np_index.py] index refreshed
[se_np_index.py]np_populate completed at Fri Apr  3 02:44:43 2015
 (elapsed time in hr:min:sec: 4:00:59.872092)

Note: cs 2005 may be missing applications that were published in later years
This should be rerun from Marc's later more complete repository

CS 2000:
>>> es_np_index.np_populate("i_cs_2000", "computers", "ln-us-A21-computers", 2000, 2000, 10000, True, True, 0) 
[se_np_index.py]np_populate started at Fri Apr  3 07:45:26 2015

WARNING:elasticsearch:HEAD /i_cs_2000 [status:404 request:0.002s]
[es_np_index.py] created np index: i_cs_2000
[es_np_index.py] created data generator for bulk loading
[tv_filepath]file: /home/j/anick/patent-classifier/ontology/roles/data/patents/ln-us-A21-computers/data/tv/
Fri Apr  3 07:45:26 2015        0       [es_np.py gen_bulk_lists]Starting make_bulk_lists for years: 2000 2000

[tv_filepath]file: /home/j/anick/patent-classifier/ontology/roles/data/patents/ln-us-A21-computers/data/tv/
[es_np_index.py] Bulk loaded sublist 1
[es_np_index.py] Bulk loaded sublist 2...

[es_np_index.py] Bulk loaded sublist 4134
Fri Apr  3 10:19:57 2015        0       [es_np_index.py]Completed make_bulk_lists for years: 2000 2000. Number of lines: 49098194

[gen_bulk_lists]49098194 lines from 22701 files written to index i_cs_2000
[es_np_index.py] Bulk loaded sublist 4135
[es_np_index.py] bulk loading completed
[es_np_index.py] index refreshed
[se_np_index.py]np_populate completed at Fri Apr  3 10:19:57 2015
 (elapsed time in hr:min:sec: 2:34:31.839746)

CS 2002

>>> es_np_index.np_populate("i_cs_2002", "computers", "ln-us-A21-computers", 2002, 2002, 10000, True, True, 0) 
[se_np_index.py]np_populate started at Fri Apr  3 16:33:03 2015

WARNING:elasticsearch:HEAD /i_cs_2002 [status:404 request:0.002s]
[es_np_index.py] created np index: i_cs_2002
[es_np_index.py] created data generator for bulk loading
[tv_filepath]file: /home/j/anick/patent-classifier/ontology/roles/data/patents/ln-us-A21-computers/data/tv/
Fri Apr  3 16:33:03 2015        0       [es_np.py gen_bulk_lists]Starting make_bulk_lists for years: 2002 2002

[tv_filepath]file: /home/j/anick/patent-classifier/ontology/roles/data/patents/ln-us-A21-computers/data/tv/
[es_np_index.py] Bulk loaded sublist 1

[es_np_index.py] Bulk loaded sublist 14443
Sat Apr  4 19:08:41 2015        0       [es_np_index.py]Completed make_bulk_lists for years: 2002 2002. Number of lines: 167741898

[gen_bulk_lists]167741898 lines from 36676 files written to index i_bio_2002
[es_np_index.py] Bulk loaded sublist 14444
[es_np_index.py] bulk loading completed
[es_np_index.py] index refreshed
[se_np_index.py]np_populate completed at Sat Apr  4 19:08:41 2015
 (elapsed time in hr:min:sec: 9:48:28.665183)


Naming convention for indices will be i_<domain>_<year>
So we need to alias the i_bio index to be specific to year 2003

curl -XPOST 'http://localhost:9200/_aliases' -d '
{
    "actions" : [
        { "add" : { "index" : "i_bio", "alias" : "i_bio_2003" } }
    ]
}'


##############################################################
4/10/15 corpus statistics for biomed patents year 2003
Redoing after rebuilding index with cphr and phr

/home/j/anick/patent-classifier/ontology/roles/data/patents/ln-us-A27-molecular-biology/data/term_features/2003
[anick@sarpedon 2003]$ ls -1 | wc -l
38343

# nc data is now in /home/j/anick/patent-classifier/ontology/roles/data/nc/

# subdirectory bio_2003

# Search ES for all instances of a 3 word phrase.  Return a list of [phr doc_id] pairs
res = es_np_query.qmamf_long(l_query_must=[["length", 3]],l_fields=["doc_id", "phr", "cphr"], index_name="i_bio_2003") 

# Using the result r, write out the phrase and doc_id data for length 3 instances to trigrams.inst
# l_fieldtypes are the python print statement data types (e.g. "s" for "%s").  You need one per field, in correct order.
es_np_query.dump_rfields(res, l_fieldnames=["cphr", "phr", "doc_id"], l_fieldtypes=["s", "s", "s"], output_file="/home/j/anick/patent-classifier/ontology/roles/data/nc/bio_2003/trigrams.inst")

[anick@sarpedon bio_2003]$ wc -l trigrams.inst
5904129 trigrams.inst

# apply the illegal phrase filter to the length 3 instances
# to produce trigrams.inst.filt
cat trigrams.inst | egrep '^[a-z]' | python2.7 /home/j/anick/patent-classifier/ontology/roles/filter_phr_doc_file.py

[anick@sarpedon bio_2003]$ wc -l trigrams.inst.filt
3988629 trigrams.inst.filt
([anick@sarpedon roles]$ wc -l bio.2003.3.inst.filt2
2126633 bio.2003.3.inst.filt2 )  note: old version did not include background sections

# sort uniq to get document frequencies rather than collection frequencies
cat trigrams.inst.filt | cut -f1,3 | sort | uniq > trigrams.inst.filt.su

[anick@sarpedon bio_2003]$ wc -l trigrams.inst.filt.su
2303675 trigrams.inst.filt.su
([anick@sarpedon roles]$ wc -l trigrams.inst.filt.su
1320668 bio.2003.3.inst.filt2.su )

# get doc freq of each phrase, sort by number reverse
cat trigrams.inst.filt.su | cut -f1 | sortuc1 | sortnr > trigrams.inst.filt.su.f1.uc1.nr

# How many triples only occur in one doc?
[anick@sarpedon bio_2003]$ cat trigrams.inst.filt.su.f1.uc1.nr | egrep '^1      ' | wc -l
715209
([anick@sarpedon roles]$ cat trigrams.inst.filt2.su.f1.uc1.nr | egrep '^1      ' | wc -l
333565 )

# Now do the same for bigram phrases
res = es_np_query.qmamf_long(l_query_must=[["length", 2]],l_fields=["doc_id", "phr", "cphr"], size=1000, index_name="i_bio_2003") ///

This gives an error: WARNING:elasticsearch:POST /_search/scroll?scroll=60s [status:404 request:0.270s]

The log message in /indexes/elasticsearch/logs/elasticsearch.log :

[2015-04-12 09:09:16,115][DEBUG][action.search.type       ] [John Ryker] [383] Failed to execute query phase
org.elasticsearch.search.SearchContextMissingException: No search context found for id [383]

I reran, setting size to 500.  The python process was still killed.  Log indicates:

[2015-04-12 01:16:00,502][WARN ][index.engine.internal    ] [Terrax the Tamer] [i_bio][2] failed to read latest segment infos on flush
java.io.FileNotFoundException: No such file [segments_2]

I suspect it may have run out of memory since all results were retained before writing out.  Wrote dump_ngrams to write out 
results incrementally using gen_qmamf_long and dump_gen_rfields.

es_np_query.dump_ngrams("i_bio_2003", 2, "/home/j/anick/patent-classifier/ontology/roles/data/nc/bio_2003/bigrams.inst")  
NOTE: including the background sections seems to quadruple the number of bigram occurrences (from 9,812,508 to 36,604,883)

# Do the filtering of illegal phrases (all folded into a single function now)
>>> es_np_nc.filter_phr_doc_file("/home/j/anick/patent-classifier/ontology/roles/data/nc/bio_2003/bigrams.inst")

[anick@sarpedon bio_2003]$ wc -l bigrams.inst.filt
31437309 bigrams.inst.filt

# sort uniq to get document frequencies rather than collection frequencies
cd /home/j/anick/patent-classifier/ontology/roles/data/nc/bio_2003
# At this point, we throw away the surface form of the term amd keep the
# canonical form only.
cat bigrams.inst.filt | cut -f1,3 | sort | uniq > bigrams.inst.filt.su

wc -l bigrams.inst.filt.su
15229456 bigrams.inst.filt.su

# unique bigram doc_id pairs
[anick@sarpedon roles]$ wc -l bio.2003.2.inst.filt.su
5052994 bio.2003.2.inst.filt.su


# get doc freq of each phrase, sort by number reverse
cat bigrams.inst.filt.su | cut -f1 | sortuc1 | sortnr > bigrams.inst.filt.su.f1.uc1.nr

# number of unique bigrams for the year 2003
[anick@sarpedon roles]$ wc -l bio.2003.2.inst.filt.su.f1.uc1.nr
912549 bio.2003.2.inst.filt.su.f1.uc1.nr

wc -l bigrams.inst.filt.su.f1.uc1.nr
2177289 bigrams.inst.filt.su.f1.uc1.nr

# How many bigrams only occur in one doc?
cat bigrams.inst.filt.su.f1.uc1.nr | egrep '^1       ' | wc -l
1231157

NOTES on using scan, scroll for large query result sets:
When using scan, the first set of scroll results is empty. See http://www.elastic.co/guide/en/elasticsearch/reference/1.4/search-request-scroll.html
Do we want to clear scroll between yields to release memory?  Appears to be unnecessary to do this explicitly.  By making the scroll size
small enough, memory is released automatically.
http://stackoverflow.com/questions/13464821/how-do-i-reduce-elasticsearch-scroll-response-time suggests that smaller scroll sizes are better 
both for memory use and speed.  (size is multiplied by number of shards, usually 5).

# 4/14/15 generating nc data from i_bio_2002

# Create the subdirectory for output
cd /home/j/anick/patent-classifier/ontology/roles/data/nc
mkdir bio_2002

# bigrams
es_np_query.dump_ngrams("i_bio_2002", 2, "/home/j/anick/patent-classifier/ontology/roles/data/nc/bio_2002/bigrams.inst")  
wc -l bigrams.inst
36604883 bigrams.inst

# trigrams
es_np_query.dump_ngrams("i_bio_2002", 3, "/home/j/anick/patent-classifier/ontology/roles/data/nc/bio_2002/trigrams.inst")  


# Do the filtering of illegal phrases (all folded into a single function now)
>>> es_np_nc.filter_phr_doc_file("/home/j/anick/patent-classifier/ontology/roles/data/nc/bio_2002/bigrams.inst")

>>> es_np_nc.filter_phr_doc_file("/home/j/anick/patent-classifier/ontology/roles/data/nc/bio_2002/trigrams.inst")

wc -l trigrams.inst.filt
wc -l bigrams.inst.filt


# sort uniq to get document frequencies rather than collection frequencies
cd /home/j/anick/patent-classifier/ontology/roles/data/nc/bio_2002
# At this point, we throw away the surface form of the term amd keep the
# canonical form only.
cat trigrams.inst.filt | cut -f1,3 | sort | uniq > trigrams.inst.filt.su
cat bigrams.inst.filt | cut -f1,3 | sort | uniq > bigrams.inst.filt.su

wc -l trigrams.inst.filt.su
wc -l bigrams.inst.filt.su

///
# get doc freq of each phrase, sort by number reverse
cat trigrams.inst.filt.su | cut -f1 | sortuc1 | sortnr > trigrams.inst.filt.su.f1.uc1.nr
cat bigrams.inst.filt.su | cut -f1 | sortuc1 | sortnr > bigrams.inst.filt.su.f1.uc1.nr

# number of unique trigrams for the year 2002
wc -l trigrams.inst.filt.su.f1.uc1.nr
wc -l bigrams.inst.filt.su.f1.uc1.nr

# How many trigrams only occur in one doc?
cat trigrams.inst.filt.su.f1.uc1.nr | egrep '^1       ' | wc -l
cat bigrams.inst.filt.su.f1.uc1.nr | egrep '^1       ' | wc -l

---------------------
4/21/15
Build i_bio_1997

Now try to create the full bio 1997 index:
>>> es_np_index.np_populate("i_bio_1997", "biology", "ln-us-A27-molecular-biology", 1997, 1997, 5000, True, True, 0) 

output of index creation:

Tue Apr 21 21:23:23 2015        0       [es_np_index.py]Completed make_bulk_lists for years: 1997 1997. Number of lines: 42859083

[gen_bulk_lists]42859083 lines from 11894 files written to index i_bio_1997
[es_np_index.py] Bulk loaded sublist 6970
[es_np_index.py] bulk loading completed
[es_np_index.py] index refreshed
[se_np_index.py]np_populate completed at Tue Apr 21 21:23:24 2015
 (elapsed time in hr:min:sec: 2:53:17.896356)

NOTE bio_2002 and 2003 appear to have identical data.  2002 is incorrect because the index_name 2003 was hardwired into a query function!

#  create trigram and bigram output for 1997


# trigrams
es_np_query.dump_ngrams("i_bio_1997", 3, "/home/j/anick/patent-classifier/ontology/roles/data/nc/bio_1997/trigrams.inst")  
# I added pos to the output, let's test by running a few:
es_np_query.dump_ngrams("i_bio_1997", 3, "/home/j/anick/patent-classifier/ontology/roles/data/nc/bio_1997/trigrams.inst.pos")

I added filtering of illegal phrases to dump_ngrams.  Let's try that:
es_np_query.dump_ngrams("i_bio_1997", 3, "/home/j/anick/patent-classifier/ontology/roles/data/nc/bio_1997/trigrams.inst.filt")

# bigrams
es_np_query.dump_ngrams("i_bio_1997", 2, "/home/j/anick/patent-classifier/ontology/roles/data/nc/bio_1997/bigrams.inst.filt")  
///
wc -l bigrams.inst
36604883 bigrams.inst

wc -l trigrams.inst.filt
wc -l bigrams.inst.filt


# sort uniq to get document frequencies rather than collection frequencies
cd /home/j/anick/patent-classifier/ontology/roles/data/nc/bio_1997
# At this point, we throw away the surface form of the term amd keep the
# canonical form only.

cat trigrams.inst.filt | grep "JJ " | cut -f1,3 | sort | uniq > trigrams.inst.filt.JJ.su
# NN will be any ngram that does not include a JJ.  Note that FW is typically a noun tag (foreign word)
cat trigrams.inst.filt | grep -v "JJ " | cut -f1,3 | sort | uniq > trigrams.inst.filt.NN.su

cat bigrams.inst.filt | grep "JJ " | cut -f1,3 | sort | uniq > bigrams.inst.filt.JJ.su
cat bigrams.inst.filt | grep -v "JJ " | cut -f1,3 | sort | uniq > bigrams.inst.filt.NN.su

DO it for all
cat trigrams.inst.filt | cut -f1,3 | sort | uniq > trigrams.inst.filt.su
cat bigrams.inst.filt | cut -f1,3 | sort | uniq > bigrams.inst.filt.su

wc -l trigrams.inst.filt.su
wc -l bigrams.inst.filt.su

# get doc freq of each phrase, sort by number reverse
cat trigrams.inst.filt.NN.su | cut -f1 | sortuc1 | sortnr > trigrams.inst.filt.NN.su.f1.uc1.nr
cat bigrams.inst.filt.NN.su | cut -f1 | sortuc1 | sortnr > bigrams.inst.filt.NN.su.f1.uc1.nr

cat trigrams.inst.filt.JJ.su | cut -f1 | sortuc1 | sortnr > trigrams.inst.filt.JJ.su.f1.uc1.nr
cat bigrams.inst.filt.JJ.su | cut -f1 | sortuc1 | sortnr > bigrams.inst.filt.JJ.su.f1.uc1.nr

# all data
cat trigrams.inst.filt.su | cut -f1 | sortuc1 | sortnr > trigrams.inst.filt.su.f1.uc1.nr
cat bigrams.inst.filt.su | cut -f1 | sortuc1 | sortnr > bigrams.inst.filt.su.f1.uc1.nr

# number of unique trigrams for the year 1997
wc -l trigrams.inst.filt.su.f1.uc1.nr
wc -l bigrams.inst.filt.su.f1.uc1.nr

# How many trigrams only occur in one doc?
cat trigrams.inst.filt.su.f1.uc1.nr | egrep '^1       ' | wc -l
cat bigrams.inst.filt.su.f1.uc1.nr | egrep '^1       ' | wc -l

#Compute trigram statistics
# NN
es_np_nc.trigram2info("/home/j/anick/patent-classifier/ontology/roles/data/nc/bio_1997", "trigrams.inst.filt.NN.su.f1.uc1.nr" , "bigrams.inst.filt.NN.su.f1.uc1.nr") 

# all
es_np_nc.trigram2info("/home/j/anick/patent-classifier/ontology/roles/data/nc/bio_1997", "trigrams.inst.filt.su.f1.uc1.nr" , "bigrams.inst.filt.su.f1.uc1.nr")

TODO: Check whether any NN and JJ terms overlap.  We may not be able to compute stats correctly if we separate out the phrase types early.
TODO: add gene sequences to illegal terms in canon.py  (done)
Conclusion: it is better to filter out JJ triples at the end, since they may be interpreted differently in different docs.

///
es_np_nc.trigram2info("/home/j/anick/patent-classifier/ontology/roles/data/nc/bio_1997", "trigrams.inst.filt.su.f1.uc1.nr" , "bigrams.inst.filt.su.f1.uc1.nr") 

#Redo trigram stats for 2003 (note that we haven't divided 2003 data into NN and JJ phrases)
es_np_nc.trigram2info("/home/j/anick/patent-classifier/ontology/roles/data/nc/bio_2003", "trigrams.inst.filt.su.f1.uc1.nr" , "bigrams.inst.filt.su.f1.uc1.nr") 

# Run the growth function (after adjusting file names accordingly in the function!)
es_np_nc.run_dump_growth() 

#This creates a growth file in eval dir: /home/j/anick/patent-classifier/ontology/roles/data/nc/eval

cd /home/j/anick/patent-classifier/ontology/roles/data/nc/eval
cat growth.bio_1997_2003.stats | sortnr -k3 | cut -f1,2,3,4,5,6,12,14,15,21 > growth.bio_1997_2003.stats.sorted_summary

.stats contains: (phr, df3gram, dfab, dfbc, dfac, raw_diff, ratio, bibranch, top_gram, bracketing)
growth contains: phr diff diff_ratio df ab bc ac ab-bc ab/bc bb(Y/N) tg(B,T) br(LRU) df ab bc ac ab-bc ab/bc bb(Y/N) tg(B,T) br(LRU)
                 1   2    3          4  5  6  7  8     9     10      11      12      13 14 15 16 17    18    19      20      21

cat growth.bio_1997_2003.stats | sortnr -k3 | cut -f1,2,3,4,10,11,12,13,19,20,21 > growth.bio_1997_2003.stats.sorted_summary

#######################################
4/23/15
By comparing doc_freq sizes in i_bio_2003 with trigrams.inst.filt.doc_id, I found that the data for bio_2003 is incorrect.
hence rerunning!

trigrams
es_np_query.dump_ngrams("i_bio_2003", 3, "/home/j/anick/patent-classifier/ontology/roles/data/nc/bio_2003/trigrams.inst.filt")

# bigrams
es_np_query.dump_ngrams("i_bio_2003", 2, "/home/j/anick/patent-classifier/ontology/roles/data/nc/bio_2003/bigrams.inst.filt")  
///
wc -l bigrams.inst
36604883 bigrams.inst

wc -l trigrams.inst.filt
wc -l bigrams.inst.filt

Functions below can be run using bash script in local directory

/home/j/anick/patent-classifier/ontology/roles/grams.sh   

# sort uniq to get document frequencies rather than collection frequencies
cd /home/j/anick/patent-classifier/ontology/roles/data/nc/bio_2003
# At this point, we throw away the surface form of the term amd keep the
# canonical form only.

cat trigrams.inst.filt | grep "JJ " | cut -f1,3 | sort | uniq > trigrams.inst.filt.JJ.su
# NN will be any ngram that does not include a JJ.  Note that FW is typically a noun tag (foreign word)
cat trigrams.inst.filt | grep -v "JJ " | cut -f1,3 | sort | uniq > trigrams.inst.filt.NN.su

cat bigrams.inst.filt | grep "JJ " | cut -f1,3 | sort | uniq > bigrams.inst.filt.JJ.su
cat bigrams.inst.filt | grep -v "JJ " | cut -f1,3 | sort | uniq > bigrams.inst.filt.NN.su

DO it for all
cat trigrams.inst.filt | cut -f1,3 | sort | uniq > trigrams.inst.filt.su
cat bigrams.inst.filt | cut -f1,3 | sort | uniq > bigrams.inst.filt.su

wc -l trigrams.inst.filt.su
wc -l bigrams.inst.filt.su

# get doc freq of each phrase, sort by number reverse
cat trigrams.inst.filt.NN.su | cut -f1 | sortuc1 | sortnr > trigrams.inst.filt.NN.su.f1.uc1.nr
cat bigrams.inst.filt.NN.su | cut -f1 | sortuc1 | sortnr > bigrams.inst.filt.NN.su.f1.uc1.nr

cat trigrams.inst.filt.JJ.su | cut -f1 | sortuc1 | sortnr > trigrams.inst.filt.JJ.su.f1.uc1.nr
cat bigrams.inst.filt.JJ.su | cut -f1 | sortuc1 | sortnr > bigrams.inst.filt.JJ.su.f1.uc1.nr

# all data
cat trigrams.inst.filt.su | cut -f1 | sortuc1 | sortnr > trigrams.inst.filt.su.f1.uc1.nr
cat bigrams.inst.filt.su | cut -f1 | sortuc1 | sortnr > bigrams.inst.filt.su.f1.uc1.nr

# number of unique trigrams for the year 2003
wc -l trigrams.inst.filt.su.f1.uc1.nr
wc -l bigrams.inst.filt.su.f1.uc1.nr

# How many trigrams only occur in one doc?
cat trigrams.inst.filt.su.f1.uc1.nr | egrep '^1       ' | wc -l
cat bigrams.inst.filt.su.f1.uc1.nr | egrep '^1       ' | wc -l

#Compute trigram statistics
# NN
es_np_nc.trigram2info("/home/j/anick/patent-classifier/ontology/roles/data/nc/bio_2003", "trigrams.inst.filt.NN.su.f1.uc1.nr" , "bigrams.inst.filt.NN.su.f1.uc1.nr") 

# all
es_np_nc.trigram2info("/home/j/anick/patent-classifier/ontology/roles/data/nc/bio_2003", "trigrams.inst.filt.su.f1.uc1.nr" , "bigrams.inst.filt.su.f1.uc1.nr")

TODO: Check whether any NN and JJ terms overlap.  We may not be able to compute stats correctly if we separate out the phrase types early.
TODO: add gene sequences to illegal terms in canon.py  (done)
Conclusion: it is better to identify JJ triples at the end, since they may be interpreted differently in different docs.

Use grams.sh to run the next operations (massaging ngrams files) in the respective ngram directories.


4/26/15

#Redo trigram stats for 2003 (note that we haven't divided 2003 data into NN and JJ phrases)
es_np_nc.trigram2info("/home/j/anick/patent-classifier/ontology/roles/data/nc/bio_2003", "trigrams.inst.filt.su.f1.uc1.nr" , "bigrams.inst.filt.su.f1.uc1.nr") 


# Run the growth function (after adjusting file names accordingly in the function!)
es_np_nc.run_dump_growth() 

#This creates a growth file in eval dir: /home/j/anick/patent-classifier/ontology/roles/data/nc/eval
///
cd /home/j/anick/patent-classifier/ontology/roles/data/nc/eval

.stats contains: (phr, df3gram, dfab, dfbc, dfac, raw_diff, ratio, bibranch, top_gram, bracketing)
bb(Y/N) is it bibranching?
tg(B,T) is the trigram or at least one bigram more frequent?
br(LRU) based on AB, BC, is the phrase left, right, or undecided branching?
growth contains: phr diff diff_ratio df ab bc ac ab-bc ab/bc bb(Y/N) tg(B,T) br(LRU) df ab bc ac ab-bc ab/bc bb(Y/N) tg(B,T) br(LRU)
                 1   2    3          4  5  6  7  8     9     10      11      12      13 14 15 16 17    18    19      20      21

cat growth.bio_1997_2003.stats | sortnr -k3 | cut -f1,2,3,4,10,11,12,13,19,20,21 > growth.bio_1997_2003.stats.sorted_summary

summary contains:
term                            diff diff_ratio df     bb      tg      br       df     bb      tg      br          
biological library approach     307     0.9935  2       Y       B       R       309     N       B       L
1                               2       3       4       5       6       7       8       9       10      11

left vs. right branching:

[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.sorted_summary | cut -f1,5,6,7,9,10,11 | cut -f1,4,7 | grep "L    L" | wc -l
45446
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.sorted_summary | cut -f1,5,6,7,9,10,11 | cut -f1,4,7 | grep "L    R" | wc -l
2592
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.sorted_summary | cut -f1,5,6,7,9,10,11 | cut -f1,4,7 | grep "R    L" | wc -l
2300
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.sorted_summary | cut -f1,5,6,7,9,10,11 | cut -f1,4,7 | grep "R    R" | wc -l
103690

unknown
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.sorted_summary | cut -f1,5,6,7,9,10,11 | cut -f1,4,7 | grep "U    U" | wc -l
9003
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.sorted_summary | cut -f1,5,6,7,9,10,11 | cut -f1,4,7 | grep "U    R" | wc -l
4895
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.sorted_summary | cut -f1,5,6,7,9,10,11 | cut -f1,4,7 | grep "U    L" | wc -l
2347
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.sorted_summary | cut -f1,5,6,7,9,10,11 | cut -f1,4,7 | grep "L    U" | wc -l
859
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.sorted_summary | cut -f1,5,6,7,9,10,11 | cut -f1,4,7 | grep "R    U" | wc -l
1246

top gram
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.sorted_summary | cut -f1,6,10 | grep "B   B" | wc -l
150374
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.sorted_summary | cut -f1,6,10 | grep "T   T" | wc -l
13042
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.sorted_summary | cut -f1,6,10 | grep "T   B" | wc -l
5745
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.sorted_summary | cut -f1,6,10 | grep "B   T" | wc -l
3217

bibranching
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.sorted_summary | cut -f1,5,9 | grep "Y    Y" | wc -l
9793
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.sorted_summary | cut -f1,5,9 | grep "N    N" | wc -l
151794
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.sorted_summary | cut -f1,5,9 | grep "N    Y" | wc -l
5845
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.sorted_summary | cut -f1,5,9 | grep "Y    N" | wc -l
4946

top gram for 2003 comparing most freq 5000 to all
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.sorted_summary.sort_df_2003 | head -5000 | cut -f1,6,10 | grep "B B" | wc -l
3845
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.sorted_summary.sort_df_2003 | head -5000 | cut -f1,6,10 | grep "T T" | wc -l
778
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.sorted_summary.sort_df_2003 | head -5000 | cut -f1,6,10 | grep "B T" | wc -l
282
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.sorted_summary.sort_df_2003 | head -5000 | cut -f1,6,10 | grep "T B" | wc -l
95
top 5000 in 2003:
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.sorted_summary.sort_df_2003 | head -5000 | cut -f1,10 | grep "B" | wc -l
3940
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.sorted_summary.sort_df_2003 | head -5000 | cut -f1,10 | grep "T" | wc -l
1060
overall:
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.sorted_summary.sort_df_2003 | cut -f1,10 | grep "B" | wc -l
156119
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.sorted_summary.sort_df_2003 | cut -f1,10 | grep "T" | wc -l
16259

Among most frequent terms, 27% are trigram favored terms
Among all, 10% are trigram favored

2003 bibranching
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.sorted_summary.sort_df_2003 | head -5000 | cut -f1,9 | grep "Y" | wc -l
651
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.sorted_summary.sort_df_2003 | head -5000 | cut -f1,9 | grep "N" | wc -l
4349
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.sorted_summary.sort_df_2003 | cut -f1,9 | grep "N" | wc -l
156740
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.sorted_summary.sort_df_2003 | cut -f1,9 | grep "Y" | wc -l
15638

Among most frequent terms: 15% are bibranching, 
Among all: 10%

To filter files with awk
cd /home/j/anick/patent-classifier/ontology/roles/data/nc/eval

cat <file> | awk -F <delimiter tab> '$<field> <relation> <value>' | more 
To get output delimiter to be tab: {OFS = FS}
and: &&
or: ||


# Create a subset of terms with 1997 count = 1 and 2003 count >= 10
# output is not sorted by field 14 (doc freq in 2003)
cat growth.bio_1997_2003.stats.cat | awk -F $'\t' 'BEGIN {OFS = FS} $4 == 1 && $14>=10'  > growth.bio_1997_2003.stats.cat.1_10

# 
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.cat.1_10 | cut -f25 | sort | uniq -c | sort -nr | more
    846 LLLLNB_NNN
    674 RRRRNB_JNN
    602 RRRRNB_JJN
    533 LLLLNB_JNN
    352 RRRRNB_NNN
    247 RRLLNB_NNN
    224 RRLLNB_JNN
    173 RRRRNB_NJN
    120 RRUUNB_JNN
    115 RRUUNB_NNN
     99 RRUUNB_JJN
...

# number of different categories
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.cat.1_10 | cut -f25 | sort | uniq -c | sort -nr | wc -l
309
# number of noun-only categories
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.cat.1_10 | grep -v "J" | cut -f25 | sort | uniq -c | sort -nr | wc -l
109

# create a subset of 1000 nouns-only with highest frequency
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.cat | grep NNN | sortnr -k14 | head -1000 > growth.bio_1997_2003.stats.cat.N.1000
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.cat.N.1000 | cut -f25 | sort | uniq -c | sortnr -k1 > growth.bio_1997_2003.stats.cat.N.1000.su
[anick@sarpedon eval]$ more growth.bio_1997_2003.stats.cat.N.1000.su
    321 LLLLNB_NNN
    125 RRRRNB_NNN
     98 RRLLNB_NNN
     73 LLLLNT_NNN
     55 RRRRNT_NNN
     53 RRLLYB_NNN


# cases where Adjacency and Dependency models differ:
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.cat.N.1000 | grep RRLLNB_NNN | cut -f1,15,16,17,18,19,25 | more
translation termination codon   138     1222    10      -1084   -128    RRLLNB_NNN
Defintion of termination codon includes termination, so BC is a shorter form of ABC
Question for annotators: Does BC imply ABC?
We could use entropy to test for this.
Interpretation could follow from whether Adj and Dep agree or disagree and how:
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.cat | grep " termination codon" | grep J | cut -f1,14,25 | more 
translational termination codon 22      RRLLNB_JNN # this is the definitional long form
native termination codon        1       RRRRNB_JNN # adjective refers to codon
natural termination codon       4       RRRRNB_JNN
suppressible termination codon  4       RRRRNB_JNN
premature termination codon     37      RRLLNB_JNN # the premature refers to termination

[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.cat | grep " termination codon" | grep -v J | cut -f1,14,25 | more 
opal termination codon  2       RRRRNB_NNN 
tga termination codon   6       RRRRNB_NNN
chain termination codon 6       RRLLNB_NNN # definitional
amber termination codon 2       RRRRNB_NNN
suppressor termination codon    1       RRRRNB_NNN
tag termination codon   5       RRRRNB_NNN
translation termination codon   366     RRLLNB_NNN # definitional
taa termination codon   12      RRRRNB_NNN
transcription termination codon 4       RRLLYB_NNN

# bibranching cases
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.cat.1_10 | grep '[A-Z]Y' | grep -v J | cut -f1,14,15,16,17,25 | sortnr -k2 | more
plant gene promoter     33      504     304     855     LLRRYB_NNN

plant gene promoter = plant promoter  (promoter implies gene)

blood serum concentration       34      447     601     474     RRLRYB_NNN  (serum implies blood)


TODO: replace the canonical form with a surface form to avoid showing truncated phrases for evaluation.  Use the most frequent surface 
variant in year 2.

First create a file with variant frequencies for the year (2003)
cd /home/j/anick/patent-classifier/ontology/roles/data/nc/bio_2003
cat trigrams.inst.filt | cut -f1,2 | sortuc1 > trigrams.inst.filt.variants.uc


Evaluation comments:
For compounds involving adjectival modifiers, mark a phrase as not a concept if the modifier isn't part of
a concept.

not-a-concept
single active compound
larger molecular structure
comparable water-in-oil emulsion
less inhibitory effect

concepts:
non-coding regulatory sequence
mature protein portion
abnormal blood vessel
oleic acid diglyceride
pulmonary viral infection
cmv-infected human fibroblast

misparsed phrase (not-a-phrase)
molecular weight characteristic


Maybe we can remove a lot of these by looking for frequent first terms?
No, most of them could be part of a legit compound.

cat growth.bio_1997_2003.stats.cat.1_10 | grep -v J > growth.bio_1997_2003.stats.cat.1_10.N
cat growth.bio_1997_2003.stats.cat.1_10 | grep J > growth.bio_1997_2003.stats.cat.1_10.J
-rw-r--r-- 1 anick grad   313857 Apr 29 17:11 growth.bio_1997_2003.stats.cat.1_10.N
-rw-r--r-- 1 anick grad   491961 Apr 29 17:12 growth.bio_1997_2003.stats.cat.1_10.J

# generate samples (adjust files and paramaters)
es_np_nc.run_nc_cat_sample_N()    
es_np_nc.run_nc_cat_sample_J()

These create:
-rw-r--r-- 1 anick grad   313857 Apr 29 20:12 growth.bio_1997_2003.stats.cat.1_10.N.3300
-rw-r--r-- 1 anick grad   430763 Apr 29 20:15 growth.bio_1997_2003.stats.cat.1_10.J.3300    

Now create a summary file and annotation file (just the surface forms)
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.cat.1_10.N.3300 | cut -f1,4,14,25,26 > growth.bio_1997_2003.stats.cat.1_10.N.3300.condensed
[anick@sarpedon eval]$ cat growth.bio_1997_2003.stats.cat.1_10.N.3300 | cut -f26 > growth.bio_1997_2003.stats.cat.1_10.N.3300.annot

DOCUMENTATION 4/29/15

I have created several files to summarize noun compound data in preparation for annotation.
All are based on a subset of terms for which their 1997 doc_freq = 1 and 2003 doc_freq >= 10.
Out of this subset of terms, I extracted those made up of nouns only and took a diverse sample
of 3300 terms.

Files are in /home/j/anick/patent-classifier/ontology/roles/data/nc/eval

file: growth.bio_1997_2003.stats.cat.1_10.N.3300.condensed contains
<canonical_form> <1997_doc_freq> <2003_doc_freq> <category> <surface_form>

canonical_form is often the surface form but could be truncated in rare cases.  We will
presentonly  surface forms for evaluation by annotators.

The category field (e.g., LLRRYB_NNN) is composed of the following one-letter fields:
1. bracketing prediction {L,R} using simple raw bigram adjacency (diff AB - BC) 1997
2. bracketing prediction using simple raw dependency (diff AC - AB) 1997
3. bracketing prediction using simple raw adjacency (diff AB - BC) 2003
4. bracketing prediction using simple raw dependency (diff AC - AB) 2003
5. Bibranching in 2003? {Y,N}
6. Does trigram or some component bigram have highest frequency in 2003? {T,B}
After the underscore is the part-of-speech signature of the component words (e.g., _NNN)

The file is sorted to maximize diversity of categories at the front, so annotation should start
at the front, in case we don't get to do the entire set.  Number of terms is 3300.  Assuming a 10%
bad phrase rate, we will still get 3000 good phrases to annotate.

file: growth.bio_1997_2003.stats.cat.1_10.N.3300.cat_freq counts terms
by category and sorts categories by frequency.  The head of the file is:
846     LLLLNB_NNN
352     RRRRNB_NNN
247     RRLLNB_NNN
115     RRUUNB_NNN
88      RRLLYB_NNN
88      LLLLYB_NNN ....

Based on the simple measures, left bracketing exceeds right by more than 2:1.

file: growth.bio_1997_2003.stats.cat.1_10.N.3300.annot
contains the terms alone, in diversity order, without other fields

We should do a few ourselves and compare bracketing.  Based on our experience, we should create annotation
guidelines that are easy to follow, including examples.  In addition to bracketing, we need to ask about
bibranching and whether the trigram is an established concept (as in cases where trigram frequency exceeds 
component bigram frequencies).


-----------------
rewrite

I have created several files to summarize noun compound data in preparation for annotation.
All are based on a subset of trigrams for which their 1997 doc_freq = 1 and their 2003 doc_freq >= 10.

This allows us to explore bracketing for the same term when "rare" and "more common".
Out of this subset of terms, I extracted those trigrams made up of nouns only and took a diverse sample
of 3300 terms.  (I can make up a similar set later for compounds including adjectives.)

Files are in /home/j/anick/patent-classifier/ontology/roles/data/nc/eval

FILE: growth.bio_1997_2003.stats.cat.1_10.N.3300.condensed

contains  <canonical_form> <1997_doc_freq> <2003_doc_freq> <category> <surface_form>

canonical_form is often the surface form but could be truncated in rare cases.  We will
presentonly  surface forms for evaluation by annotators.

The category field (e.g., LLRRYB_NNN) is composed of the following one-letter fields:
1. bracketing prediction {L,R,U} using simple raw bigram adjacency (diff AB - BC) 1997
2. bracketing prediction using simple raw dependency (diff AC - AB) 1997
3. bracketing prediction using simple raw adjacency (diff AB - BC) 2003
4. bracketing prediction using simple raw dependency (diff AC - AB) 2003
5. Bibranching in 2003? {Y,N}
6. Does trigram or some component bigram have highest frequency in 2003? {T,B}
After the underscore is the part-of-speech signature of the component words (e.g., _NNN)

The file is sorted to maximize diversity of categories at the front, so annotation should start
at the front, in case we don't get to do the entire set.  Number of terms is 3300.  Assuming a 10%
bad phrase rate, we will still get 3000 good phrases to annotate.

FILE: growth.bio_1997_2003.stats.cat.1_10.N.3300.cat_freq

shows the frequency of each category.  The head of the file is shown here:
846     LLLLNB_NNN
352     RRRRNB_NNN
247     RRLLNB_NNN
115     RRUUNB_NNN
88      RRLLYB_NNN
88      LLLLYB_NNN ....

Based on the simple measures, left bracketing exceeds right by more than 2:1.

FILE: growth.bio_1997_2003.stats.cat.1_10.N.3300.annot
contains the terms alone, in diversity order, without other fields

We should do a few ourselves and compare bracketing.  Based on our experience, we should try to create annotation guidelines that are easy to follow, including examples.  In addition to bracketing, we need to ask about bibranching and whether the trigram is an established concept (as in cases where trigram frequency exceeds component bigram frequencies).



