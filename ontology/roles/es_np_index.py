# es_np.py
# elasticsearch indexing of np chunks
# PGA 1/17/15
# see http://exploringelasticsearch.com/searching_data.html for examples
# original version of this file moved into es_np_index_20150328.py

# goals
# Do canonicalization outside of es
# make loc and integer
# create parent-child relationship between term occurrences and documents
# add a sentence type with the heads of all phrases in the sentence, to check for co-occurring head terms
# use new interface to fuse repository


from elasticsearch import Elasticsearch
es = Elasticsearch()

import roles_config
import pnames
import os
import sys
import re
import codecs
import pdb
import math
import copy
import time
from datetime import timedelta

from collections import defaultdict
# log is our own log routines for timing runs
import log
from ontology.utils.file import get_year_and_docid, open_input_file

import logging
logging.basicConfig()
# from http://excid3.com/blog/no-handlers-could-be-found-for-logger/
# What this does is imports the same logging module as the library does and it sets up a configuration application wide that the s logging import can use to write messages properly.plugin

# control messages output
verbose_p = False

fuse_corpus_root = roles_config.FUSE_CORPUS_ROOT
corpus_root = roles_config.CORPUS_ROOT

from elasticsearch import Elasticsearch
es = Elasticsearch()

import canon
# make a canonicalizer object containing an English lexicon
can = canon.Canon()

# general es utils

def refresh_index(index_name):
    #important! refresh index after loading
    es.indices.refresh(index=index_name)

# meta for bulk_loading
def format_d_action(index_name, type_name, uid, parent_id=None):
    d_action = { "index":{"_index": index_name ,"_type": type_name, "_id": uid, "parent": parent_id }} 
    return(d_action)

# mapping and index creation

# patterns for matching specific features in a phr_feats line
# doc_loc value is the sentence number in the patent, starting at 0
p_doc_loc = re.compile('doc_loc=([^\s]*)' )
p_prev_V = re.compile('prev_V=([^\s]*)' )
p_prev_J = re.compile('prev_J=([^\s]*)' )
p_prev_Npr = re.compile('prev_Npr=([^\s]*)' )
p_section = re.compile('section_loc=([^\_\s]*)' )
p_pos = re.compile('tag_sig=([^\s]*)' )


# for mapping examples, see http://exploringelasticsearch.com/searching_usernames_and_tokenish_text.html 
# for parent-child examples, see http://obtao.com/blog/2014/04/elasticsearch-advanced-search-and-nested-objects/
#   http://stackoverflow.com/questions/11806584/treat-child-as-field-of-parent-in-elastic-search-query
#   http://stackoverflow.com/questions/27553916/how-to-return-the-count-of-unique-documents-by-using-elasticsearch-aggregation
# For parent/child queries to work, a child must be on the same shard as the parent, so routing information
# about the id of the parent must be included on the index line of the child when loading.  Children can be
# loaded before the parent.  
# e.g. { "index": { "_id": "london", "parent": "uk" }} where the parent field gives the id of the parent
# See http://www.elastic.co/guide/en/elasticsearch/guide/current/grandparents.html#grandparents
def create_np_index(index_name):
    d_np_schema = {
        "settings": {
            "analysis": {
                        
                # we want our analyzers to preserve punctuation, which we use as 
                # term boundary markers in some fields ([|])
                # phrase fields are pre-tokenized using whitespace as separator, so we don't 
                # need to do any fancier tokenization in elasticsearch.
                
                "analyzer": {
                    "analyzer_wl_only": {
                        "type": "custom",
                        "tokenizer" : "whitespace",
                        "filter" : ["lowercase"]
                        }
                    }}},

        # "np" here is the type of object to be indexed
        # for index options, see http://www.elasticsearch.org/guide/en/elasticsearch/guide/current/stopwords-phrases.html#index-options
        
        # all stemming/lemmatization is done externally
        # term, phr, prev_Npr, prev_V, prev_J are surface forms (not canonicalized)
        "mappings":{
            "doc": {"properties":
                        {
                    "domain":{"type":"string","index":"not_analyzed", "index_options":"docs"},
                    "year":{"type":"integer","index": "not_analyzed", "index_options":"docs"},
                    "doc_id":{"type":"string","index":"not_analyzed", "index_options":"docs"},
                    }
                    },
            "sent": {
                # parent and child need to be routed to the same shard
                "_parent": {
                    "type" : "doc",
                    "identifier": "doc_id", #optional as id is the default value
                    "property" : "doc" #optional as the default value is the type
                    },
                "properties": {
                    # meta info
                    # this duplicates some parent fields, allowing us to avoid the join when not needed
                    "section":{"type":"string","index":"not_analyzed","index_options":"docs"},
                    "domain":{"type":"string","index":"not_analyzed", "index_options":"docs"},
                    "year":{"type":"integer","index": "not_analyzed", "index_options":"docs"},
                    "doc_id":{"type":"string","index":"not_analyzed", "index_options":"docs"},
                    "loc":{"type":"integer","index": "not_analyzed", "index_options":"docs"},
                    # heads of np's in the same sentence
                    # implemented as a list of strings, identified by the field name "shead" 
                    "sheads": {"type":"string","analyzer":"analyzer_wl_only", "index_options":"docs", "index_name":"shead"},
                    "sterms":{"type":"string","analyzer":"analyzer_wl_only", "index_options":"docs", "index_name":"sterm"},
                    },
                },
            
            "np": {
                # parent and child need to be routed to the same shard
                "_parent": {
                    "type" : "doc",
                    "identifier": "doc_id", #optional as id is the default value
                    "property" : "doc" #optional as the default value is the type
                    },

                "properties": {
                    # cterm is NP with _ separating words, so each term is a single token
                    "cterm":{"type":"string","index":"not_analyzed","index_options":"docs"},
                    # phr is NP with whitespace separating words
                    "phr":{"type":"string","index":"not_analyzed","index_options":"docs"},
                    # cphr is canonical NP with whitespace separating words
                    "cphr":{"type":"string","index":"not_analyzed","index_options":"docs"},
                    # sp is separated phrase: cphr with | separating words and start and end brackets ([])
                    "sp":{"type":"string","analyzer":"analyzer_wl_only","index_options":"offsets"},
                    # syntactic relations
                    # "c" or "s" at the beginning indicates the head word has been canonicalized
                    "cprev_Npr":{"type":"string","index":"not_analyzed","index_options":"docs"},
                    # separated previous noun/prep  ("combination of")
                    "spn":{"type":"string","analyzer":"analyzer_wl_only","index_options":"offsets"},
                    # previous verb/prep ("used by")
                    "prev_V":{"type":"string","index":"not_analyzed","index_options":"docs"},
                    # canonicalized previous verb/prep ("use by")
                    "cprev_V":{"type":"string","index":"not_analyzed","index_options":"docs"},
                    # separated previous verb/prep ("[ use | by ]")
                    "spv":{"type":"string","analyzer":"analyzer_wl_only","index_options":"offsets"},
                    "prev_J":{"type":"string","index":"not_analyzed","index_options":"docs"},
                    # part of speech tags for the phrase
                    "pos":{"type":"string","analyzer":"analyzer_wl_only","index_options":"docs"},
                    # components of cphr
                    "chead":{"type":"string","index":"not_analyzed","index_options":"docs"},
                    # meta info
                    # this duplicates some parent fields, allowing us to avoid the join when not needed
                    "section":{"type":"string","index":"not_analyzed","index_options":"docs"},
                    "domain":{"type":"string","index":"not_analyzed", "index_options":"docs"},
                    "year":{"type":"integer","index": "not_analyzed", "index_options":"docs"},
                    "doc_id":{"type":"string","index":"not_analyzed", "index_options":"docs"},
                    "loc":{"type":"integer","index": "not_analyzed", "index_options":"docs"},
                    # length is number of words in a phrase
                    "length":{"type":"integer","index": "not_analyzed", "index_options":"docs"},
                    # parts of speech, as one string (e.g. JJ_NN_NN)
                    "pos":{"type":"string","index": "not_analyzed", "index_options":"docs"},
                    # section, as one string (e.g. ABSTRACT)
                    "section":{"type":"string","index": "not_analyzed", "index_options":"docs"},
                   },
                }
            }
        }
    
    np_index = es.indices.create(index=index_name, body=d_np_schema)
    return(d_np_schema)

#####################################################################
# index population

# create a dictionary that matches the schema 

# Given a phrase with separator char = split_char,
# create a bracketed phrase with "|" as internal separator
# e.g., "web server software" => "[ web | server | software ]"
def make_separated_phrase(phrase, split_char=" "):
    sp = phrase.replace(split_char, " | ")
    sp = "[ " + sp + " ]"
    return(sp)

# create a dictionary that matches the schema for type "doc"
def format_doc_d_content(domain, year, patent_id):
    d_content = {'domain': domain, 'year': int(year), 'doc_id': patent_id}
    return(d_content)

def format_sent_d_content(domain, year, patent_id, section, loc, sheads, sterms):
    d_content = {'domain': domain, 'year': int(year), 'doc_id': patent_id, 'section': section, 'loc': loc, 'sheads': sheads, 'sterms': sterms}
    return(d_content)

# create a dictionary that matches the schema for type "np"
# phr, pos are white space separated
# prev_V, prev_Npr are _ separated
def format_np_d_content(phr, prev_Npr, prev_V, prev_J, domain, year, doc_id, loc, section, pos):
    d_content = {"phr": phr, 'domain': domain, 'year': int(year), 'doc_id': doc_id, 'loc': int(loc), 'section': section, 'pos': pos}
    # add the remaining fields (if they exist)
    # length = number of tokens in the phrase
    l_tokens = phr.split(" ")
    d_content["length"] = len(l_tokens)
    #pdb.set_trace()
    
    cphr = can.get_canon_np(phr)
    l_cphr = cphr.split(" ")
    sp = make_separated_phrase(cphr, split_char=" ")

    d_content["sp"] = sp
    d_content["phr"] = phr
    d_content["cphr"] = cphr
    # cterm is the canonicalized phrase as a single token 
    d_content["cterm"] = cphr.replace(" ", "_")

    # head is the last word in a canonicalized NP
    d_content["chead"] = l_cphr[-1]

    if prev_Npr != None:
        prev_Npr = prev_Npr.replace("_", " ")
        c_prev_Npr = can.get_canon_npr(prev_Npr)
        d_content["cprev_Npr"] = c_prev_Npr
        spn = make_separated_phrase(c_prev_Npr, split_char="_")
        d_content["spn"] = spn
    if prev_V != None:
        
        prev_V = prev_V.replace("_", " ")
        c_prev_V = can.get_canon_vp(prev_V)
        d_content["prev_V"] = prev_V
        d_content["cprev_V"] = c_prev_V
        spv = make_separated_phrase(c_prev_V, split_char="_")
        d_content["spv"] = spv
    if prev_J != None:
        # note: no canonicalization of adjectives at the moment
        d_content["prev_J"] = prev_J

    # for debugging the contents of a record's dictionary when bulk loading
    ####print "d_content: %s\n" % d_content
    return(d_content)

# make bulk loading list for test3 db
def test3_make_bulk():
    index_name = "test3"
    type_name = "np"

    # list of elements for bulk loading, alternating action and content objects
    l_bulk_elements = []

    i = 0

    l_doc_id = ["pat1", "pat1", "pat2"]
    domain = "cs"
    year = 2000
    l_loc = [100, 200, 300]
    l_term = ["first word term", "second words terms", "third wording"]
    l_prev_Npr = ["tops_of", "top_of", "topping_of"]
    l_prev_V = ["dig_up", "digging_up", "digs_up"]
    l_prev_J = ["", "", "big"]

    for loc in l_loc:

        uid = str(i)
        term = l_term[i]
        loc = l_loc[i]
        doc_id = l_doc_id[i]
        prev_Npr = l_prev_Npr[i]
        prev_V = l_prev_V[i]
        prev_J = l_prev_J[i]
        l_bulk_elements.append(format_d_action(index_name, type_name, uid, parent="p1"))
        l_bulk_elements.append(format_np_d_content(term, prev_Npr, prev_V, prev_J, domain, year, doc_id, loc))

        i += 1    
    
    return(l_bulk_elements)

#es_np_index.test3_populate()
def test3_populate():
    index_name = "test3"
    l_bulk_elements = test3_make_bulk()

    # if we try to create an index which exists already, the elastic search will throw an error,
    # hence need to check if exists, and if exists - delete the index
    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name)
        
    res = create_np_index(index_name)
    res = es.bulk(l_bulk_elements)
    refresh_index(index_name)
    print "load completed into index %s" % index_name


##################################

# make bulk lists as a python generator
# r = es_np.gen_bulk_lists("i_testg", "np", "computers", "ln-us-A21-computers", 1997, 1997, 2, True, False, 9)
def gen_bulk_lists(index_name, type_name, domain, corpus, start, end, lines_per_bulk_load=100, section_filter_p=True, write_to_file_p=False, max_lines=0):
    # reading from fuse pipeline data
    # writing to local tv corpus dir
    # for years from start to end

    # we'll need the name of the pipeline step to create the directory path to 
    # the phr_feats files.
    pipeline_step = "d3_phr_feats"

    ###print "corpus_root: %s, corpus: %s"  % (corpus_root, str(corpus))

    # range parameters
    start_year = int(start)
    end_year = int(end)
    start_range = start_year
    end_range = end_year + 1

    # track the time in <year>.log
    log_file = pnames.tv_dir_year_file(corpus_root, corpus, "all", "log")
    s_log = open(log_file, "w")

    log_message = "[es_np.py gen_bulk_lists]Starting make_bulk_lists for years: " + str(start) + " " + str(end)
    time = log.log_current_time(s_log, log_message, True)
    # remember the start_time for computing total time
    start_time = time

    # we'll bulk load all the data for a single year.
    # the argument to elasticsearch bulk is a list of dictionaries
    # alternating metadata and content.  We'll build this up in l_bulk_elements
    
    # The output is a list of flattened paired elements, where each list contains the meta/content elements for n lines
    #l_bulk_lists = []
    l_bulk_elements = []

    for year in range(start_range, end_range):

        # loop through files in file_list_file for the year
        filelist_file = pnames.fuse_filelist(fuse_corpus_root, corpus, year)
        s_file_list = open(filelist_file)

        # track the number of lines output to json file
        num_lines_output = 0
        json_file = pnames.tv_dir(corpus_root, corpus) + str(year) + ".chunks.json"
        s_json = codecs.open(json_file, "w", encoding='utf-8')

        file_count = 0
        ###pdb.set_trace()

        for line in s_file_list:
            ###pdb.set_trace()


            file_count += 1
            
            line = line.strip("\n")
            # get the date/filename portion of path
            l_line_fields = line.split("\t")
            # get the rest of the file path (publication_year/id.xml)
            pub_year_and_file = l_line_fields[2]
            # extract patent_id from the filename (e.g. US5787464A from 1998/020/US5787464A.xml)
            patent_id = os.path.splitext(os.path.basename(pub_year_and_file))[0]

            # create a "doc" type entry to be bulk loaded.  This will be the parent of both "sent"
            # and "np" records in the index
            
            l_bulk_elements.append(format_d_action(index_name, "doc", patent_id))
            l_bulk_elements.append(format_doc_d_content(domain, year, patent_id))

            # lists to capture each sent's sheads and sterms
            sheads = []
            sterms = []
            # loc is the sentence number in the document, starting at 0
            current_sent = 0
            # Assume the initial section will be TITLE
            current_section = "TITLE"

            num_lines_output += 1

            # end creating doc index entry

            phr_feats_file = pnames.fuse_phr_feats_file(fuse_corpus_root, corpus, pipeline_step, year, pub_year_and_file)

            #print "[invention]opening phr_feats: %s, id: %s" % (phr_feats_file, patent_id)
            #sys.exit()

            #s_phr_feats = codecs.open(phr_feats_file, encoding='utf-8')
            # handle compressed or uncompressed files
            s_phr_feats = open_input_file(phr_feats_file)

            for line in s_phr_feats:

                # if we have reached the line limit for a single bulk api call, add the sublist to l_bulk_lists 
                # and start a new sublist
                if (num_lines_output % lines_per_bulk_load) == 0:
                    ###print "num_lines_output: %i" % num_lines_output
                    # mod will be 0 for initial time through loop, so ignore this sublist
                    if l_bulk_elements != []:
                        yield l_bulk_elements
                        l_bulk_elements = []

                # todo make into regex ///
                # Note that DESC was added 3/38/15, so indices created earlier do not contain that section.
                if not(section_filter_p) or line.find("TITLE") > 0 or line.find("ABSTRACT") > 0 or line.find("SUMMARY") > 0 or line.find("DESC") > 0:
                    # then process the line
                    l_data = line.split("\t")
                    # chunk is phrase with  blanks connecting tokens
                    uid = l_data[0]  # uid is doc_id + phrase number
                    phr = l_data[2]  # phrase with whitespace separating words

                    # extract the value field from the doc_loc feature to get the loc (sentence number)
                    loc = p_doc_loc.search(line).group(1)
                    # We will store it as an integer in es
                    loc = int(loc)

                    section = p_section.search(line).group(1)
                    pos = p_pos.search(line).group(1)
                    pos = pos.replace("_", " ")

                    # populate chunk dictionaries
                    prev_V = p_prev_V.search(line)
                    if prev_V != None:
                        # extract the matched string (group 0 is the entire match, while 
                        # group 1 is the first parenthesized subexpression in the pattern)
                        prev_V = prev_V.group(1)

                    prev_Npr = p_prev_Npr.search(line)
                    if prev_Npr != None:
                        prev_Npr = prev_Npr.group(1)

                    prev_J = p_prev_J.search(line)
                    if prev_J != None:
                        # extract the matched string (group 0 is the entire match, while 
                        # group 1 is the first parenthesized subexpression in the pattern)
                        prev_J = prev_J.group(1)


                    ###pdb.set_trace()
                    l_bulk_elements.append(format_d_action(index_name, "np", uid, parent_id=patent_id))
                    d_field_content = format_np_d_content(phr, prev_Npr, prev_V, prev_J, domain, year, patent_id, loc, section, pos)
                    l_bulk_elements.append(d_field_content)

                    # We will use data in d_field_content to avoid recomputing fields for sent.
                    shead = d_field_content["chead"]
                    sterm = d_field_content["cterm"]
                    # section can change whenever loc changes
                    section = d_field_content["section"]

                    # if loc != current_sent, we need to store a sent record for the current_loc
                    if loc != current_sent:
                        # store the record and start populating a new one
                        sent_id = patent_id + "_" + str(current_sent)
                        l_bulk_elements.append(format_d_action(index_name, "sent", sent_id, parent_id=patent_id))
                        l_sent_dict = format_sent_d_content(domain, year, patent_id, current_section, current_sent, sheads, sterms)
                        l_bulk_elements.append(l_sent_dict)

                        ###print "Adding sent: %s, sent_dict: %s" % (sent_id, l_sent_dict)
                        # re-initialize the sheads and sterms lists
                        sheads = [ shead ]
                        sterms = [ sterm ]
                        # increment count for "sent" output
                        num_lines_output += 1
                        # update the current_sent and section
                        current_sent = loc
                        current_section = section

                    else:
                        # we are still in the same sentence.
                        # add the latest term/head to the sent fields for current_sent
                        sheads.append(shead)
                        sterms.append(sterm)

                    # increment count for "np" output
                    num_lines_output += 1
       
                # stop after max_lines files for debugging
                ###print "num_lines_output: %i, max_lines: %i" % (num_lines_output, max_lines)
                if (max_lines != 0) and num_lines_output > max_lines: 
                    break
            # break out of file loop as well
            if (max_lines != 0) and num_lines_output > max_lines: 
                break

            # We need to store a sent record for the last sentence in last file (= current_sent)
            sent_id = patent_id + "_" + str(current_sent)
            ###print "[gen_bulk_list]last sent_id: %s, sheads: %s, sterms: %s\n" % (sent_id, sheads, sterms)
            l_bulk_elements.append(format_d_action(index_name, "sent", sent_id, parent_id=patent_id))
            l_bulk_elements.append(format_sent_d_content(domain, year, patent_id, current_section, current_sent, sheads, sterms))
            num_lines_output += 1

            s_phr_feats.close()            

        s_json.close()

    log_message = "[es_np_index.py]Completed make_bulk_lists for years: " + str(start) + " " + str(end) + ". Number of lines: " + str(num_lines_output)
    time = log.log_current_time(s_log, log_message, True)

    s_log.close()
    s_file_list.close()

    # yield the last remaining l_bulk_elements

    print "[gen_bulk_lists]%i lines from %i files written to index %s" % (num_lines_output, file_count, index_name)
    yield(l_bulk_elements)

# Lists are too long to process as a single list. Use generator to mix bulk list creation and indexing
# got timeout error withe docs_per_bulk_load=500
# es_np.np_populate("i_np", "computers", "ln-us-A21-computers", 1997, 1997, 100, True, True, 3)
# es_np.np_populate("i_np_bio", "biology", "ln-us-A27-molecular-biology", 2003, 2003, 5000, True, True, 0)
# small test:
# es_np.np_populate("i_testg", "biology", "ln-us-A27-molecular-biology", 2003, 2003, 2, True, True, 9)
# es_np_index.np_populate("i_test1", "biology", "ln-us-A27-molecular-biology", 2003, 2003, 50, True, True, 1000)

# i_nps is np index with stemming applied to the sp* fields
# es_np.np_populate("i_nps_bio", "biology", "ln-us-A27-molecular-biology", 2003, 2003, 50000, True, True, 0)
# The raw data is located here: 
# /home/j/anick/patent-classifier/ontology/roles/data/patents/ln-us-A27-molecular-biology/data/term_features/2003
# Number of patents in year 2003: 38343

# indices are stored here
# [anick@sarpedon 1]$ cd /indexes/elasticsearch/data/elasticsearch/nodes/0/indices/

# new index with doc, np, sent object types 3/30/15
# full db: es_np_index.np_populate("i_bio", "biology", "ln-us-A27-molecular-biology", 2003, 2003, 10000, True, True, 0)
# we will alias i_bio to i_bio_2003
# todo: es_np_index.np_populate("i_bio_2002", "biology", "ln-us-A27-molecular-biology", 2002, 2002, 10000, True, True, 0)


#  ACT/PN info in /home/j/anick/patent-classifier/ontology/roles/data/patents/ln-us-A21-computers/data/tv
# full db: es_np_index.np_populate("i_cs_2005", "computers", "ln-us-A21-computers", 2005, 2005, 10000, True, True, 0)
# full db: es_np_index.np_populate("i_cs_2002", "computers", "ln-us-A21-computers", 2002, 2002, 10000, True, True, 0)


def np_populate(index_name, domain, corpus, start_year, end_year, lines_per_bulk_load=5000, section_filter_p=True, new_index_p=True, max_lines=0):

    populate_start_time = time.time()
    localtime = time.asctime( time.localtime(populate_start_time) )
    print "[se_np_index.py]np_populate started at %s\n" % localtime
    
    # type of document (needed for es mapping)
    type_name = "np"
                                               
    if new_index_p:

        # First create new index with mapping:
        # if we try to create an index which exists already, the elastic search will throw an error,
        # hence need to check if exists, and if exists - delete the index
        if es.indices.exists(index=index_name):
            es.indices.delete(index=index_name)

        # create empty index
        # res = es.indices.create(index="test1", body=try_createBody)

        res = create_np_index(index_name)
        print "[es_np_index.py] created np index: %s" % index_name

    # now bulk load data
    # first create a generator to produce the list of elements for bulk loading
    bulk_generator = gen_bulk_lists(index_name, type_name, domain, corpus, start_year, end_year, lines_per_bulk_load, section_filter_p=True, max_lines=max_lines)
    ###pdb.set_trace()
    print "[es_np_index.py] created data generator for bulk loading"
    ### print "[es_np_index.py] l_bulk_lists: %s" % (l_bulk_lists)

    # Now load each sublist of elements into elasticsearch
    num_sublists = 0
    for l_bulk_elements in bulk_generator:
        num_sublists += 1
        res = es.bulk(l_bulk_elements)
        print "[es_np_index.py] Bulk loaded sublist %i" % num_sublists
    print "[es_np_index.py] bulk loading completed"

    # and refresh the index
    refresh_index(index_name)
    print "[es_np_index.py] index refreshed"

    populate_end_time = time.time()
    localtime = time.asctime( time.localtime(populate_end_time) )
    elapsed_time = populate_end_time - populate_start_time
    pp_elapsed_time = str(timedelta(seconds=elapsed_time))
    print "[se_np_index.py]np_populate completed at %s\n (elapsed time in hr:min:sec: %s)\n" % (localtime, pp_elapsed_time)
    
""""
Queries to test the index population

# sent
>>> r = es_np_query.qmamf(l_query_must=[["shead", "receptor"],["shead", "antibody"]], doc_type="sent", size=10000, query_type="search", index_name="i_testg") 

# np
>>> r = es_np_query.qmamf(l_query_must=[["cphr", "amino acid sequence"]], doc_type="np", size=10000, query_type="search", index_name="i_testg", l_fields=["doc_id"]) 

# sent as child
>>> r = es_np_query.qpmamf(l_query_must=[["shead", "trail"]], doc_type="doc", child_type="sent", size=3, query_type="search", index_name="i_testg") 

# np as child
>>> r = es_np_query.qpmamf(l_query_must=[["chead", "trail"]], doc_type="doc", child_type="np", size=3, query_type="search", index_name="i_testg") 





"""
