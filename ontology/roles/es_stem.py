# es_stem.py
# test stemmer and retaining punctuation

from elasticsearch import Elasticsearch
es = Elasticsearch()

import logging
import os
import sys
import re
import codecs
from collections import defaultdict


#  {"analysis":{"analyzer": {"whitespace":{"type": "pattern","lowercase":"false","pattern":"\\s+"}}}}\

# sample mapping, testing stemmers, keeping punctuation.
def create_ts_index(index_name):
    d_ts_schema = {
        "settings": {
            "analysis": {
                "filter": {
                    "stemmer_eng_v": {
                        "type": "stemmer",
                        "name": "porter2" },
                    "stemmer_eng_n": {
                        "type": "stemmer",
                        "name": "minimal_english" 
                        #"name": "light_english" 
                        }
                    },
                        
                "analyzer": {
                    "analyzer_whitespace": {
                        "type": "pattern",
                        "lowercase":"true",
                        "pattern":"\\s+" },
                    "analyzer_eng_v": {
                        "type": "custom",
                        "tokenizer" : "whitespace",
                        "filter" : ["lowercase", "stemmer_eng_v"]
                        },
                    "analyzer_eng_n": {
                        "type": "custom",
                        "tokenizer" : "whitespace",
                        "filter": ["lowercase", "stemmer_eng_n"] }
                }}},
                   
        # "ts" here is the type of object to be indexed
        # for index options, see 
        # http://www.elasticsearch.org/guide/en/elasticsearch/guide/current/stopwords-phrases.html#index-options
        
        "mappings":{"ts":{"properties": {
                    
                    "phr_v":{"type":"string","analyzer":"analyzer_eng_v","index_options":"offsets"},
                    "phr_n":{"type":"string","analyzer":"analyzer_eng_n","index_options":"offsets"},
                    "phr":{"type":"string","analyzer":"analyzer_whitespace","index_options":"offsets"},
                    "year":{"type":"integer","index": "not_analyzed","index_options":"docs"}
                    }}}
        }

    ts_index = es.indices.create(index=index_name, body=d_ts_schema)
    return(d_ts_schema)

def refresh_index(index_name):
    #important! refresh index after loading
    es.indices.refresh(index=index_name)

# Given a phrase with separator char = split_char,
# create a bracketed phrase with "|" as internal separator
# e.g., "web server software" => "[ web | server | software ]"
def make_separated_phrase(phrase, split_char=" "):
    sp = phrase.replace(split_char, " | ")
    sp = "[ " + sp + " ]"
    return(sp)

# meta for bulk_loading
def format_d_action(index_name, type_name, uid):
    d_action = { "index":{"_index": index_name ,"_type": type_name, "_id": uid }} 
    return(d_action)

def format_ts_d_content(phr, phr_v, phr_n, year):
    d_content ={'phr': phr, 'phr_n' : phr_n, 'phr_v' : phr_v, 'year': year}
    return(d_content)

# make bulk loading list
def test_stemming_make_bulk():
    index_name = "test_stemming"
    type_name = "ts"

    # list of elements for bulk loading, alternating action and content objects
    l_bulk_elements = []

    i = 0

    # testing whether we can store nested list object without indexing it
    l_phr_v = ["run up", "runs up", "running up", "ran up"]
    l_phr_n = ["run for", "runs for", "running for", "flies for"]
    l_phr = ["monkey for", "monkies for", "monkeying for", "monkeys for"]
    year = 2000

    for phr in l_phr:

        uid = str(i)
        phr = l_phr[i]
        phr_v = l_phr_v[i]
        phr_n = l_phr_n[i]

        phr = make_separated_phrase(phr, split_char=" ")
        phr_v = make_separated_phrase(phr_v, split_char=" ")
        phr_n = make_separated_phrase(phr_n, split_char=" ")
        
        l_bulk_elements.append(format_d_action(index_name, type_name, uid))
        l_bulk_elements.append(format_ts_d_content(phr, phr_v, phr_n, year))

        i += 1    
    
    return(l_bulk_elements)

#es_stem.test_stemming_populate()
def test_stemming_populate():
    index_name = "test_stemming"
    l_bulk_elements = test_stemming_make_bulk()

    # if we try to create an index which exists already, the elastic search will throw an error,
    # hence need to check if exists, and if exists - delete the index
    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name)
        
    res = create_ts_index(index_name)
    res = es.bulk(l_bulk_elements)
    refresh_index(index_name)
    print "test_stemming load completed"

# l_must is a list of [property, value] pairs
def make_must_term_list(l_must):
    l_must_term = []
    for pair in l_must:
        l_must_term.append({"term" : { pair[0] : pair[1] }})
    return(l_must_term)

### query shorcut
## es_stem.qmaf("phr", "process | for")
def qmaf(field, value, l_must=[], doc_type="ts", index_name="test_stemming", query_type="search"):
    
    l_must_term = make_must_term_list(l_must)

    ###print "[qmaf] l_must_term: %s" % l_must_term
    queryBody = {
        "query": {
            "constant_score" : {
                "query" : {
                    "filtered" : {
                        "query": {
                            "match_phrase" : { field : value }
                            },
                        "filter": {
                            "bool": {
                                "must" : l_must_term
                                }
                            }
                        }
                    },
                # boost is a child of constant_score
                "boost" : 1.0
            }
        }
     }

    ###print "[qmaf] queryBody: %s" % queryBody

    if query_type == "search":
        res = es.search(index=index_name, doc_type = doc_type, body=queryBody, size=100000)
    elif query_type == "count":
        res = es.count(index=index_name, doc_type = doc_type, body=queryBody)
    return(res)

