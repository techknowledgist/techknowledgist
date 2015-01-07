# based on http://elasticsearch-py.readthedocs.org/en/master/

# todo
# tokenize sentences to be consistent with Stanford tagger
# add more timing to log

import roles_config
import pnames
import os
import sys
import re
import codecs
from collections import defaultdict
# log is our own log routines for timing runs
import log

from ontology.utils.file import get_year_and_docid, open_input_file

import logging
logging.basicConfig()
# from http://excid3.com/blog/no-handlers-could-be-found-for-logger/
# What this does is imports the same logging module as the library does and it sets up a configuration application wide that the s logging import can use to write messages properly.plugin

fuse_corpus_root = roles_config.FUSE_CORPUS_ROOT
corpus_root = roles_config.CORPUS_ROOT

from elasticsearch import Elasticsearch
es = Elasticsearch()

# pattern for matching the doc_loc feature in a phr_feats line
# doc_loc value is the sentence number in the patent, starting at 0
p_doc_loc = re.compile('doc_loc=([^\s]*)' )
p_prev_V = re.compile('prev_V=([^\s]*)' )
p_prev_Npr = re.compile('prev_Npr=([^\s]*)' )

"""
# example docs for testing elasticsearch

doc1 = {
'patent': 'xyz1.xml',
'year': '1997',
'sentence': "At last, we placed the ring cap cleaner into the cat food bag, all-at-once.",
'chunks': "ring_cap_cleaner cat_food_bag",
'sent': '1'
}

doc2 = {
'patent': 'xyz2.xml',
'year': '1998',
'sentence': "we found the ring cap cleaner inside the dog's house.",
'chunks': "ring_cap_cleaner dog_'_house",
'sent': '1'
}

doclist = [doc1, doc2]
"""

# analyzers used in schemas (defined here for compactness in schema definitions)
MyFilter = {"MyFilter":{"type":"trim"}}
MyAnalyzer = {"MyAnalyzer":{"type":"custom","tokenizer":"letter","filter":"MyFilter"}}
catAnalyzer = {"catAnalyzer":{"type":"pattern", "tokenizer":"keyword","pattern":"#"}}
whitesAnalyzer = {"whitespace":{"type": "pattern","lowercase":"false","pattern":"\\\\s+"}}

#whitePuncAnalyzer = {"whitespace":{"type": "pattern","lowercase":"false","pattern":"\\\\s+"}}


# schema
# settings: declares the analyzers to be used
# mappings: associate analyzers and types with fields

"""
try_createBody = {"settings":\
                 {"analysis":{"analyzer":{"catAnalyzer":{"type":"pattern", "tokenizer":"keyword","pattern":"#"},\
                                          "whitespace":{"type": "pattern","lowercase":"false","pattern":"\\s+"}}}}\
                      # "doc" here is the type of object to be indexed
                  ,"mappings":{"doc":{"properties":\
                                         {"patent":{"type":"string", "index": "not_analyzed"  ,"index_options":"offsets"},\
                                          "sentence":{"type":"string","index_options":"offsets"},\
                                          "chunks":{"type":"string","analyzer":"whitespace","index_options":"offsets"},\
                                          "year":{"type":"integer","index": "not_analyzed","index_options":"offsets"},\
                                          "sent":{"type":"integer","index": "not_analyzed","index_options":"offsets"},\
                                          }}}}

# First create new index with mapping:
# if we try to create an index which exists already, the elastic search will throw an error,
# hence need to check if exists, and if exists - delete the index
if es.indices.exists(index="test1"):
    es.indices.delete(index="test1")

# create empty index
# res = es.indices.create(index="test1", body=try_createBody)

# query

def qs(query):
    queryBody = {"query":{"match":{"sentence": query}},\
                     "highlight":{"fields":{"sentence":{}}, "number_of_fragments" : 1000000}}
    res = es.search(index="test1", doc_type = 'doc', body=queryBody, size="10")
    print("<<<Got %d Hits, here are the Hits from the first 10 documents:>>>" % res['hits']['total'])
    res_idx = 0
    for r in res['hits']['hits']:
        #print ("r: %s" % r)
        print ("sentence: %s" % (r['_source']['sentence']))
        res_idx += 1
    return(res)
"""

def create_colloc_index(index_name):
    d_colloc_schema = {"settings":\
                 {"analysis":{"analyzer": {"whitespace":{"type": "pattern","lowercase":"false","pattern":"\\s+"}}}}\
                 # "colloc" here is the type of object to be indexed
                  ,"mappings":{"colloc":{"properties":\
                                         {"i":{"type":"string", "index": "not_analyzed"  ,"index_options":"offsets"},\
                                          "c":{"type":"string","analyzer":"whitespace","index_options":"offsets"},\
                                          "y":{"type":"integer","index": "not_analyzed","index_options":"offsets"},\
                                          "n":{"type":"integer","index": "not_analyzed","index_options":"offsets"},\
                                          }}}}

    colloc_index = es.indices.create(index=index_name, body=d_colloc_schema)
    return(d_colloc_schema)

def refresh_index(index_name):
    #important! refresh index after loading
    es.indices.refresh(index=index_name)


"""
# index needs a name, type, id

# Prepare action-source pairs for bulk
# pairs of actions and elements that the actions apply to
j = 0
# length of docs to be loaded in alternating list
l = 2
actions = []
while (j < l):
    # use the number of the object as the "_id" for now
    action = { "index":{"_index": "test1","_type": "doc","_id": str(j) }}
    actions.insert(j*2,action)
    action = doclist[j]
    actions.insert(j*2 + 1, action)
    j += 1

res = es.bulk(actions)

#important! refresh index after loading
es.indices.refresh(index="test1")


#------------------------
# Change query word here
#------------------------
searchWord = "Asimov"
searchWord1 = "asimov"
queryBody = {"query":{"match":{"title":'Angel Angel'}},\
             "highlight":{"fields":{"title":{}}, "number_of_fragments" : 1000000}}
res = es.search(index="books", doc_type = 'book', body=queryBody, size="10")

print("<<<Got %d Hits, here are the Hits from the first 10 documents:>>>" % res['hits']['total'])
print "\n"
"""


# meta for bulk_loading
def format_d_action(index_name, type_name, uid):
    d_action = { "index":{"_index": index_name ,"_type": type_name, "_id": uid }} 
    return(d_action)

# colloc index
# content for bulk_loading
def format_colloc_d_content(patent_id, year, sent_no, l_chunks):
    d_content = {"i": patent_id, 'y': year, 'n': sent_no, 'c': l_chunks}
    return(d_content)

# todo: replace with json call
# create a json representation of d_chunks to write to a file
def format_colloc_chunks2json(id, year, sent_no, l_chunks):
    id_string = "{" + "\"i\": " + "\"" + id + "\", "
    year_string = "'y': '" + str(year) + "', "
    sent_no_string = "'n': '" + sent_no + "', "
    chunks_string = "'c': \"" 
    for chunk in l_chunks:
        chunks_string += chunk 
        chunks_string += " "
    chunks_string += "\"}"
    json_string = id_string + year_string + sent_no_string + chunks_string
    return(json_string)

# chunk index

# content for bulk_loading
def format_chunk_d_content(year, chunk, l_docs, l_prev_V, l_prev_Npr):
    # uid=chunk_symbol, y=year, h=head, m=mod, c=chunk_symbol, d=docs, n=number_of_docs, pv=prev_V, pn=prev_Npr
    l_words = chunk.split(" ")
    head = l_words[-1]
    mod = "_".join(l_words[0:-1])
    if mod == []:
        mod = ""
    chunk_symbol = "_".join(l_words)
    number_of_docs = len(l_docs)
 
    d_content = {"c": chunk_symbol, 'y': year, 'h': head, 'm': mod, 'd': l_docs, 'n': number_of_docs, 'pv': l_prev_V, 'pn': l_prev_Npr }
    return(d_content)




# from fuse phr_feats data, create a file of the form
# patent year sent_no chunks
# in json format with attribute names: i (id), y (year), n (sent_no), c (chunks, a list)

# todo complete log file output
# format to json
# If section_filter_p is True, we limit data to lines from title, abstract and summary.
# This considerably reduces the size of data, while potentially missing some hits.

# returns a list suitable for bulk loading

# r = docs.create_json_chunks_file("computers", "colloc", "ln-us-A21-computers", 1997, 1997, 3, True, False)
def create_json_chunks_file(index_name, type_name, corpus, start, end, docs_per_bulk_load=500, section_filter_p=True, write_to_file_p=False):
    # reading from fuse pipeline data
    # writing to local tv corpus dir
    # for years from start to end

    # we'll need the name of the pipeline step to create the directory path to 
    # the phr_feats files.
    pipeline_step = "d3_phr_feats"

    # range parameters
    start_year = int(start)
    end_year = int(end)
    start_range = start_year
    end_range = end_year + 1

    # track the time in <year>.log
    log_file = pnames.tv_dir_year_file(corpus_root, corpus, "all", "log")
    s_log = open(log_file, "w")

    log_message = "Starting create_json_chunks_file for years: " + str(start) + " " + str(end)
    time = log.log_current_time(s_log, log_message, True)
    # remember the start_time for computing total time
    start_time = time


    # we'll bulk load all the data for a single year.
    # the argument to elasticsearch bulk is a list of dictionaries
    # alternating metadata and content.  We'll build this up in l_bulk_elements
    
    # The output is a list of lists, where each list contains the meta/content elements for n files
    l_colloc_bulk_lists = []
    l_colloc_bulk_elements = []

    d_chunk2prev_Npr = defaultdict(set)
    d_chunk2prev_V = defaultdict(set)
    d_chunk2doc = defaultdict(set)

    for year in range(start_range, end_range):

        # loop through files in file_list_file for the year
        filelist_file = pnames.fuse_filelist(fuse_corpus_root, corpus, year)
        s_file_list = open(filelist_file)

        # track the number of lines output to json file
        num_lines_output = 0
        json_file = pnames.tv_dir(corpus_root, corpus) + str(year) + ".chunks.json"
        s_json = codecs.open(json_file, "w", encoding='utf-8')

        file_count = 0
        for line in s_file_list:

            # if we have reached the file limit for a single bulk api call, add the sublist to l_colloc_bulk_lists 
            # and start a new sublist
            if (file_count % docs_per_bulk_load) == 0:
                # mod will be 0 for initial time through loop, so ignore this sublist
                if l_colloc_bulk_elements != []:
                    l_colloc_bulk_lists.append(l_colloc_bulk_elements)
                    l_colloc_bulk_elements = []

            file_count += 1
            
            line = line.strip("\n")
            # get the date/filename portion of path
            l_line_fields = line.split("\t")
            # get the rest of the file path (publication_year/id.xml)
            pub_year_and_file = l_line_fields[2]
            # extract patent_id from the filename (e.g. US5787464A from 1998/020/US5787464A.xml)
            patent_id = os.path.splitext(os.path.basename(pub_year_and_file))[0]
            phr_feats_file = pnames.fuse_phr_feats_file(fuse_corpus_root, corpus, pipeline_step, year, pub_year_and_file)

            #print "[invention]opening phr_feats: %s, id: %s" % (phr_feats_file, patent_id)
            #sys.exit()

            #s_phr_feats = codecs.open(phr_feats_file, encoding='utf-8')
            # handle compressed or uncompressed files
            s_phr_feats = open_input_file(phr_feats_file)

            # we need to combine all the chunks from a single sentence into one output entry
            l_chunks = []
            # assume the first sent_no in a document will always be 0
            last_sent_no = "0"
            for line in s_phr_feats:
                # todo make into regex ///
                if not(section_filter_p) or line.find("TITLE") > 0 or line.find("ABSTRACT") > 0 or line.find("SUMMARY") > 0:
                    # then process the line
                    l_data = line.split("\t")
                    # save chunk as phrase with "_" instead of blank connecting tokens
                    chunk = l_data[2].replace(" ", "_")
                    # extract the value field from the doc_loc feature to get the sent_no
                    sent_no = p_doc_loc.search(line).group(1)

                    # populate chunk dictionaries
                    d_chunk2docs[chunk].add(patent_id)
                    prev_V = p_prev_V.search(line)
                    if prev_V != None:
                        d_chunk2prev_V[chunk].add(prev_V)
                    prev_Npr = p_prev_Npr.search(line)
                    if prev_Npr != None:
                        d_chunk2prev_Npr[chunk].add(prev_Npr)

                    if sent_no == last_sent_no:
                        l_chunks.append(chunk)
                    else:
                        # we are done with the sentence, so write out the chunk list
                        json_string = format_colloc_chunks2json(patent_id, year, last_sent_no, l_chunks)
                        uid = "_".join([patent_id, last_sent_no])
                        
                        #print "last_sent_no: %s, chunks: %s, json: %s" % (last_sent_no, l_chunks, json_string)
                        # note the above print gives an error for non-asci chars.
                        if write_to_file_p:
                            # make a json file with all the data to be loaded into elasticsearch
                            s_json.write("%s\n" % json_string)
                        l_colloc_bulk_elements.append(format_d_action(index_name, type_name, uid))
                        l_colloc_bulk_elements.append(format_colloc_d_content(patent_id, year, last_sent_no, l_chunks))

                        # keep the current chunk
                        l_chunks = [chunk]
                        last_sent_no = sent_no
                        num_lines_output += 1

            # output the last line
            
            json_string = format_colloc_chunks2json(patent_id, year, last_sent_no, l_chunks)
            #print "last_sent_no: %s, chunks: %s, json: %s" % (last_sent_no, l_chunks, json_string)
            s_json.write("%s\n" % json_string)
            l_colloc_bulk_elements.append(format_d_action(index_name, type_name, uid))
            l_colloc_bulk_elements.append(format_colloc_d_content(patent_id, year, last_sent_no, l_chunks))
            num_lines_output += 1

            #"""
            # stop after n files for debugging
            if file_count > 3000:
                break
            #"""

            s_phr_feats.close()            

        # add the remaining elements to l_colloc_bulk_lists
        l_colloc_bulk_lists.append(l_colloc_bulk_elements)

        print "[docs.py]%i lines from %i files written to %s" % (num_lines_output, file_count, json_file)
        s_json.close()
    s_log.close()
    s_file_list.close()

    # prepare data for chunk index
    for chunk in d_chunk2docs.keys():
        l_docs = d_chunk2docs[chunk]
        l_prev_V = d_chunk2prev_V[chunk]
        l_prev_Npr = d_chunk2prev_Npr[chunk]

///

    return(l_colloc_bulk_lists)

# docs.populate_colloc_index("computers", "ln-us-A21-computers", 1997, 1997, 500, True, True)
def populate_colloc_index(index_name, corpus, start_year, end_year, docs_per_bulk_load=500, section_filter_p=True, new_index_p=True):

    # type of document (needed for es mapping)
    type_name = "colloc"

    if new_index_p:

        # First create new index with mapping:
        # if we try to create an index which exists already, the elastic search will throw an error,
        # hence need to check if exists, and if exists - delete the index
        if es.indices.exists(index=index_name):
            es.indices.delete(index=index_name)

        # create empty index
        # res = es.indices.create(index="test1", body=try_createBody)

        res = create_colloc_index(index_name)
        print "[docs.py] created colloc index: %s" % index_name

    # now bulk load data
    # first create the list of elements for bulk loading
    l_colloc_bulk_lists = create_json_chunks_file(index_name, type_name, corpus, start_year, end_year, docs_per_bulk_load, section_filter_p=True)
    print "[docs.py] created data for bulk loading"
    
    # Now load each sublist of elements into elasticsearch
    num_sublists = 0
    for l_colloc_bulk_elements in l_colloc_bulk_lists:
        num_sublists += 1
        res = es.bulk(l_colloc_bulk_elements)
        print "[docs.py] Bulk loaded sublist %i" % num_sublists
    print "[docs.py] bulk loading completed"

    # and refresh the index
    refresh_index(index_name)
    print "[docs.py] index refreshed"
    
#########################
# queries

def qcp(chunk, print_all_p=False):
    queryBody = {"query":{"match":{"c": chunk}},\
                     "highlight":{"fields":{"c":{}}, "number_of_fragments" : 1000000}}
    res = es.search(index="computers", doc_type = 'colloc', body=queryBody, size="10")
    print("Hits: %d" % res['hits']['total'])
    res_idx = 0
    for r in res['hits']['hits']:
        if print_all_p:
            print ("r: %s" % r)
        print ("chunks: %s" % (r['_source']['c']))
        res_idx += 1
    return(res)

def qc(chunk, index_name):
    queryBody = {"query":{"match":{"c": chunk}}}
    res = es.search(index=index_name, doc_type = 'colloc', body=queryBody, size=100000)
    return(res)

#########################
# doc colloc counts

# r = docs.get_collocs("web", "computers")
# Given the result of a query, populate collocation dicts
def get_collocs(chunk, index_name):


    # True if this chunk has already been seen in this doc
    # doc_id and chunk are combined into a key
    d_doc_colloc2seen = {}

    # count of number of docs in which a chunk is in same sentence as the given chunk
    d_colloc2count = defaultdict(int)

    res = qc(chunk, index_name)

    num_hits = len(res['hits']['hits'])  
    print "hits: %i" % num_hits

    # extract list of collocated chunks
    l_hits = res['hits']['hits']
    #print "[docs.py]l_hits: %s" % l_hits

    # store combo of patent_id and chunk in d_doc_colloc.seen
    for hit in l_hits:
        # extract doc id for the sentence
        patent_id = hit["_source"]["i"]
        #print "[docs.py]patent_id: %s" % patent_id

        # get list of collocated chunks
        l_colloc = hit["_source"]["c"]
        #print "[docs.py]l_colloc: %s" % l_colloc
        for chunk in l_colloc:
            key = "_".join([patent_id, chunk]) 
            #print "[docs.py]key: %s" % key
            if not d_doc_colloc2seen.has_key(key):
                d_doc_colloc2seen[key] = True
                # if colloc hasn't been seen before in this doc, increment count
                d_colloc2count[chunk] += 1

    # return list of collocs sorted by count
    return(sorted(d_colloc2count.items(), key = lambda (k,v): v, reverse=True))

# prev_Npr, prev_V, doc_count
