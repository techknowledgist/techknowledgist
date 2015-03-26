# esex.py
# elasticsearch tests

from elasticsearch import Elasticsearch
es = Elasticsearch()

import logging

import os
import sys
import re
import codecs
from collections import defaultdict

# tf (term_feature info)
# term year feature count [pid sent]*
# see http://www.elasticsearch.org/guide/en/elasticsearch/guide/current/mapping-intro.html
# analysis syntax example here: http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/analysis-lang-analyzer.html
def create_tf_index(index_name):
    d_tf_schema = {
        "settings": {
            "analysis": {
                "filter": {
                    "stemmer_eng_v": {
                        "type": "stemmer",
                        "name": "porter2" },
                    "stemmer_eng_n": {
                        "type": "stemmer",
                        "name": "minimal_english" }
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
                        "type": "pattern",
                        "lowercase":"true",
                        "pattern":"\\s+",
                        "filter": ["stemmer_eng_n"] }
                }},
                   
                   
            # "tf" here is the type of object to be indexed
            # for index options, see http://www.elasticsearch.org/guide/en/elasticsearch/guide/current/stopwords-phrases.html#index-options

            "mappings":{"tf":{"properties": {
                    
                        "phr_v":{"type":"string","analyzer":"analyzer_eng_v","index_options":"offsets"},\
                        "phr_n":{"type":"string","analyzer":"analyzer_eng_n","index_options":"offsets"},\
                        "phr":{"type":"string","analyzer":"analyzer_whitespace","index_options":"offsets"},\
                        "term":{"type":"string", "index": "not_analyzed"  , "index_options": "docs"},\
                        "feat":{"type":"string","index":"not_analyzed","index_options":"docs"},\
                        "year":{"type":"integer","index": "not_analyzed","index_options":"docs"},\
                        "count":{"type":"integer","index": "not_analyzed","index_options":"docs"},\
                        "locs":{"type":"object",  "enabled" : "false" }

                                          }}}}}
    

    tf_index = es.indices.create(index=index_name, body=d_tf_schema)
    return(d_tf_schema)



def create_np_index(index_name):
    d_np_schema = {"settings":\
                 {"analysis":{"analyzer": {"whitespace":{"type": "pattern","lowercase":"false","pattern":"\\s+"}}}}\
                 # "tf" here is the type of object to be indexed
                   # for index options, see http://www.elasticsearch.org/guide/en/elasticsearch/guide/current/stopwords-phrases.html#index-options

                  ,"mappings":{"np":{"properties":\
                                             # term is the NP as a single token with "_" separating words
                                             {"term":{"type":"string", "index": "not_analyzed"  , "index_options": "docs"},\
                                              # phr is NP with whitespace separating words
                                              "phr":{"type":"string","analyzer":"whitespace","index_options":"offsets"},\
                                              # syntactic relations
                                              "prev_Npr":{"type":"string","index":"not_analyzed","index_options":"docs"},\
                                              "prev_V":{"type":"string","index":"not_analyzed","index_options":"docs"},\
                                              "prev_J":{"type":"string","index":"not_analyzed","index_options":"docs"},\
                                              # components of the NP, indexed from the head back (0 to 5)
                                              "0":{"type":"string","index":"not_analyzed","index_options":"docs"},\
                                              "1":{"type":"string","index":"not_analyzed","index_options":"docs"},\
                                              "2":{"type":"string","index":"not_analyzed","index_options":"docs"},\
                                              "3":{"type":"string","index":"not_analyzed","index_options":"docs"},\
                                              "4":{"type":"string","index":"not_analyzed","index_options":"docs"},\
                                              "5":{"type":"string","index":"not_analyzed","index_options":"docs"},\
                                              # meta info
                                              "domain":{"type":"string","index":"not_analyzed","index_options":"docs"},\
                                              "year":{"type":"integer","index": "not_analyzed","index_options":"docs"},\
                                              "pid":{"type":"string","index":"not_analyzed","index_options":"docs"},\
                                              "loc":{"type":"integer","index": "not_analyzed","enabled":"false"},\

                                          }}}}


    np_index = es.indices.create(index=index_name, body=d_np_schema)
    return(d_np_schema)

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

# tf index
# content for bulk_loading
# l_locs is an unindexed list of the form [[patent_id [sent_no, sent_no, ...]], [patent_id [sent_no, sent_no, ...]]]
def format_tf_d_content(term, feat, phr, phr_v, phr_n, year, count, l_locs):
    d_content = {"term": term, 'feat': feat, 'phr': phr, 'phr_n' : phr_n, 'phr_v' : phr_v, 'year': year, 'count': count, 'locs': l_locs}
    return(d_content)


def format_np_d_content(term, prev_Npr, prev_V, prev_J, year, pid, loc):
    d_content = {"term": term, 'year': year, 'pid': pid, 'loc': loc}
    # add the remaining fields (if they exist)
    phr = term.replace("_", " ")
    d_content["phr"] = phr
    
    # generate and store the components of the np individually using as a key the relative location to the head
    i = 0
    for word in reversed(term.split("_")):
        # we don't store more than 6 words of an np
        if i >= 6:
            break
        key = str(i)
        d_content[key] = word
        i += 1

    return(d_content)


# make bulk loading list
def test1_make_bulk():
    index_name = "test1"
    type_name = "tf"

    # list of elements for bulk loading, alternating action and content objects
    l_bulk_elements = []

    i = 0

    # testing whether we can store nested list object without indexing it
    l_locs = [ [["pat1", [1]], ["pat2", [2]]], [["pat2", [2,4]], ["pat3", [3, 4]]],  [["pat3", [3,5,7], ["pat4", [4,6,8]]]] ] 
    l_term = ["term_one", "term_two", "term_three"]
    l_feat = ["prev_1", "prev_2", "prev_3"]
    l_phr_v = ["runs in", "running away", "ran around"]
    l_phr_n = ["monkey for", "monkies for", "monkeys for"]
    l_phr = ["monkey for", "monkies for", "monkeys for"]
    year = 2000
    count = [1,2,3]

    for locs in l_locs:

        uid = str(i)
        term = l_term[i]
        feat = l_feat[i]
        phr = l_phr[i]
        phr_v = l_phr_v[i]
        phr_n = l_phr_n[i]

        phr = make_separated_phrase(phr, split_char=" ")
        phr_v = make_separated_phrase(phr_v, split_char=" ")
        phr_n = make_separated_phrase(phr_n, split_char=" ")
        
        l_bulk_elements.append(format_d_action(index_name, type_name, uid))
        l_bulk_elements.append(format_tf_d_content(term, feat, phr, phr_v, phr_n, year, count, locs))

        i += 1    
    
    return(l_bulk_elements)


# make bulk loading list
def test2_make_bulk():
    index_name = "test2"
    type_name = "np"

    # list of elements for bulk loading, alternating action and content objects
    l_bulk_elements = []

    i = 0

    # testing whether we can store nested list object without indexing it
    l_locs = [ [["pat1", [1]], ["pat2", [2]]], [["pat2", [2,4]], ["pat3", [3, 4]]],  [["pat3", [3,5,7], ["pat4", [4,6,8]]]] ] 
    l_term = ["term_one", "term_two", "term_three"]
    l_feat = ["prev_1", "prev_2", "prev_3"]

    pid = "pat1"
    year = 2000
    l_loc = [100, 200, 300]
    l_term = ["number_one_term", "number_two_term", "here_is_a_third_term"]
    l_prev_Npr = ["top_of", "bottom_of", ""]
    l_prev_V = ["find", "dig_up", "find"]
    l_prev_J = ["", "", "big"]

    for locs in l_locs:

        uid = str(i)
        term = l_term[i]
        loc = l_loc[i]
        prev_Npr = l_prev_Npr[i]
        prev_V = l_prev_V[i]
        prev_J = l_prev_J[i]
        
        l_bulk_elements.append(format_d_action(index_name, type_name, uid))
        l_bulk_elements.append(format_np_d_content(term, prev_Npr, prev_V, prev_J, year, pid, loc))

        i += 1    
    
    return(l_bulk_elements)


#es_ex.test1_populate()
def test1_populate():
    index_name = "test1"
    l_bulk_elements = test1_make_bulk()

    # if we try to create an index which exists already, the elastic search will throw an error,
    # hence need to check if exists, and if exists - delete the index
    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name)
        
    res = create_tf_index(index_name)
    res = es.bulk(l_bulk_elements)
    refresh_index(index_name)
    print "test1 load completed"

#esex.test2_populate()
def test2_populate():
    index_name = "test2"
    l_bulk_elements = test2_make_bulk()

    # if we try to create an index which exists already, the elastic search will throw an error,
    # hence need to check if exists, and if exists - delete the index
    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name)
        
    res = create_np_index(index_name)
    res = es.bulk(l_bulk_elements)
    refresh_index(index_name)
    print "test2 load completed"

########
# test simple phrase match


# l_must is a list of [property, value] pairs
def make_must_term_list(l_must):
    l_must_term = []
    for pair in l_must:
        l_must_term.append({"term" : { pair[0] : pair[1] }})
    return(l_must_term)


# main function for querying NP's.
# contains a match_all query and optional set of bool filters
# does not compute rank.
# es_np.qmaf("sp", "term ]", [["year", 2000], ["doc_id", "pat1"]])
# es_np.qmaf("sp", "term ]", [["year", 2000], ["doc_id", "pat1"], ["domain", "cs"]] )
# es_np.qmaf("sp", "distortion ]", [["year", 1997], ["doc_id", "US5761382A"], ["domain", "computers"]] )
# es_ex.qmaf("phr", "run", index_name="test1", query_type="search")
def qmaf(field, value, l_must=[], doc_type="tf", index_name="test1", query_type="search"):
    
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




# esex.qm("phr", "third term", "np", "test2")
def qp(field, value, doc_type="tf", index_name="test1"):
    queryBody = {"query": {"match_phrase":{field : value}}}
    res = es.search(index=index_name, doc_type = doc_type, body=queryBody, size=100000)
    return(res)

# boolean without scoring
# esex.qm("0", "term", "1", "third", "np", "test2")
def qb(f1, v1, f2, v2, doc_type="np", index_name="test2"):

    queryBody = {
       "query" : {
          "filtered" : { 
             "filter" : {
                "bool" : {
                  "must" : [
                     { "term" : {f1 : v1}}, 
                     { "term" : {f2 : v2 }} 

                  ]

                  }
               }
             }
          }
       }
    
    res = es.search(index=index_name, doc_type = doc_type, body=queryBody, size=100000)
    return(res)


# esex.qf("phr", "third term", "np", "test2")
def qf(field, value, doc_type="tf", index_name="test1"):
    queryBody = {"query": {"filtered" : {
                             "query": { "match_all": {}},
                              
                              "filter": {
                                  "bool": {
                                     "must" : {
                                        "term" : { 
                                            field : value
                                            }

                                        }}}}}}


    res = es.search(index=index_name, doc_type = doc_type, body=queryBody, size=100000)
    return(res)


def qf2(field, value, doc_type="tf", index_name="test1"):
    queryBody = {                              
                              "filter": {
                                  "bool": {
                                     "must" : {
                                        "term" : { 
                                            field : value
                                            }

                                        }}}}


    res = es.search(index=index_name, doc_type = doc_type, body=queryBody, size=100000)
    return(res)



"""
# test range on integer value
def qr(field, value, count_min, index_name="test1"):
    queryBody = {"filter": { "bool": {
                               "must" :
                                {"term":{field : value}}, 
                               {"filter":
                          {"range": {
                              "count": { "gte":  value }
                           }}
                               }}}
                 }}

    res = es.search(index=index_name, doc_type = 'tf', body=queryBody, size=100000)
    return(res)
"""

