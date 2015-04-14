# dealing with noun compounds

from elasticsearch import Elasticsearch
es = Elasticsearch(timeout=30)

import roles_config
import pnames
import os
import sys
import re
import codecs
import pdb
import math
import copy
from collections import defaultdict
# log is our own log routines for timing runs
import log
from ontology.utils.file import get_year_and_docid, open_input_file
# for sorting dict by value
import operator

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

# override default on number of results returned for a query
max_result_size = 100000

#############################

# takes a phrase and returns a search pattern for the sp field
# phr_subset can be l(eft), r(ight), m(iddle), f(ull)
# which allows matching on the phrase as full phrase or as part
# of a larger phrase.
def phr2sp(phr, phr_subset="f"):
    l_words = phr.split(" ")
    middle = " | ".join(l_words)
    if phr_subset == "f":
        return("[ " + middle + " ]")
    elif phr_subset == "l":
        return("[ " + middle + " |")
    elif phr_subset == "r":
        return("| " + middle + " ]")
    elif phr_subset == "m":
        return("| " + middle + " |")
    else:
        return(None)
    
# head is a single noun (head of a prepositional phrase)
# phr is the word or phrase dominated by the preposition
# result is a list of two field-value pairs for matching the
# head/tail relationship in es.
# es_np.qc_mult([["spn", "[ skin" ], ["sp", "human ]" ]])
def npr2spn_sp(head, phr, phr_subset="f"):
    spn_pattern = ["spn", "[ " + head ]
    sp_pattern = ["sp", phr2sp(phr, phr_subset)]
    return([spn_pattern, sp_pattern])

# **query templates

# To test that the index has content:
# curl -XGET localhost:9200/i_nps/_search?pretty=true&q={'matchAll':{''}}
# curl -XGET localhost:9200/i_testg/_search?pretty=true&q={'matchAll':{''}}

# main function for querying NP's.
# contains a match_all query and optional set of bool filters
# does not compute rank.
# es_np.qmaf("sp", "term ]", [["year", 2000], ["doc_id", "pat1"]])
# es_np.qmaf("sp", "term ]", [["year", 2000], ["doc_id", "pat1"], ["domain", "cs"]] )
# es_np.qmaf("sp", "distortion ]", [["year", 1997], ["doc_id", "US5761382A"], ["domain", "computers"]] )
# es_np.qmaf("sp", "cell", index_name="i_np_bio", query_type="count")
# es_np.qmaf(field, value, l_must=[], doc_type="np", index_name="i_np_bio", query_type="search")
# es_np.qmaf("length", 3, l_must=[], doc_type="np", index_name="i_np_bio", query_type="search")
# es_np_query.qmaf("length", 2, index_name="test2", query_type="search")
# es_np_query.qmaf("length", 2, index_name="i_testg", query_type="search")
def qmaf(field, value, l_must=[], doc_type="np", index_name="i_nps_bio", query_type="search"):
    
    l_must_filter = make_must_filter_list(l_must)

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
                                "must" : l_must_filter
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
        res = es.search(index=index_name, doc_type = doc_type, body=queryBody, size=max_result_size)
    elif query_type == "count":
        res = es.count(index=index_name, doc_type = doc_type, body=queryBody)
    return(res)

#need return n records that contain a field value and return just the field values.

# return count of all records that have a value for a given field
# es_np.qcfhv("phr")
# es_np.qcfhv("prev_Npr")
# field has value
def qcfhv(field, doc_type="np", index_name="i_nps_bio"):
    
    query_type = "count"

    ###print "[qmaf] l_must_term: %s" % l_must_term
    queryBody = {
        "query": {
            "constant_score" : {
                "filter": {
                    "exists": {"field" : field }
                    }
                }
            }
        }

    ###print "[qmaf] queryBody: %s" % queryBody

    res = es.count(index=index_name, doc_type = doc_type, body=queryBody)["count"]
    return(res)

# f = es_np_query.rfields(r, ["phr", "doc_id"], result_type="hits")
# delist_fields_p should be True only if all field values are singletons.  It
# strips the outer list off of field values.
# if result_type is "hits", this means that we have a list of hits from elasticsearch
# (i.e. r["hits"]["hist"]).  Otherwise, we assume we have the output exactly how es 
# returns it.

# Given a result a list of field names, returns a list of field-value lists, one list for each
# result
def rfields(es_result, l_fieldnames, delist_fields_p=True, result_type="es"):
    # list of lists of values for fields in the order specified in l_fieldnames
    l_values = []
    if result_type != "hits":
        hits = es_result["hits"]["hits"]
    else:
        hits = es_result
    for res in hits:
        fields = res["fields"]
        l_values_for_res = []
        for fieldname in l_fieldnames:
            fvalue = fields[fieldname]
            if delist_fields_p:
                # remove the outer list from field value
                fvalue = fvalue[0]
            l_values_for_res.append(fvalue)
        l_values.append(l_values_for_res)
    return(l_values)

# es_np_query.dump_rfields(r, l_fieldnames=["phr", "doc_id"], l_fieldtypes=["s", "s"], output_file="bio.2000.3.inst")
def dump_rfields(es_result, l_fieldnames=[], l_fieldtypes=[], delist_fields_p=True, output_file="rfields.out", result_type="hits"):
    rf = rfields(es_result, l_fieldnames, delist_fields_p=delist_fields_p, result_type=result_type)
    s_output = codecs.open(output_file, "w", encoding='utf-8')
    for res in rf:
        i = 0
        for field in res:
            type_string = "%" + l_fieldtypes[i] + "\t"
            s_output.write(type_string % field)
            i += 1
        s_output.write("\n")
    s_output.close()


# es_np_query.dump_rfields(r_gen, l_fieldnames=["phr", "doc_id"], l_fieldtypes=["s", "s"], output_file="bio.2000.3.inst")
def dump_gen_rfields(es_result_generator, l_fieldnames=[], l_fieldtypes=[], delist_fields_p=True, output_file="rfields.out", result_type="hits"):
    s_output = codecs.open(output_file, "w", encoding='utf-8')
    res_count = 0
    for l_result in es_result_generator:
        rf = rfields(l_result, l_fieldnames, delist_fields_p=delist_fields_p, result_type=result_type)

        for res in rf:
            i = 0
            for field in res:
                type_string = "%" + l_fieldtypes[i] + "\t"
                s_output.write(type_string % field)
                i += 1
            s_output.write("\n")
            res_count += 1
        print "[dump_gen_rfields]%i results written to %s" % (res_count, output_file)
    print "[dump_gen_rfields]Completed: %i results written to %s" % (res_count, output_file)
    s_output.close()


# use of scan/scroll to handle long result sets described here:
# http://vichargrave.com/elasticsearch-client-programming-python/

# We use this approach to get around timeout errors if we try to run queries with large result
# sets directly using the es.search function.
# r = es_np_query.qmamf_long(l_query_must=[["length", 3]],l_fields=["doc_id", "phr"], size=3)
# r = es_np_query.qmamf_long(l_query_must=[["length", 2]],l_fields=["doc_id", "phr"], size=1000)
# r = es_np_query.qmamf_long(l_query_must=[["sp", "[nucleic | acid | probe]" ],l_fields=["spv", "spn"], size=10000)
# NOTE: This returns a list of "hits".

def qmamf_long(l_query_must=[], l_filter_must=[], l_fields=[], doc_type="np", index_name="i_nps_bio", size=1000, debug_p=False):

    # do the initial search to get back a scroll_id
    
    r = qmamf(l_query_must=l_query_must,l_fields=l_fields, size=size, query_type="scan", index_name=index_name, doc_type=doc_type )
    all_results = []
    scroll_size = r['hits']['total']
    #print "scroll size: %s" % scroll_size
    while (scroll_size > 0):
        try:
            #print "scroll_size: %i" % scroll_size
            #pdb.set_trace()
            all_results += r['hits']['hits']
            scroll_id = r['_scroll_id']
            #print "scroll_id: %s" % scroll_id
            r = es.scroll(scroll_id=scroll_id, scroll='60s')
            scroll_size = len(r['hits']['hits'])
        except:
            print "[qmamf_long] Exception when handling scroll_id."
            break
    return(all_results)

# for queries with very large result sets, run as a generator
def gen_qmamf_long(l_query_must=[], l_filter_must=[], l_fields=[], doc_type="np", index_name="i_nps_bio", size=500, debug_p=False):

    # do the initial search to get back a scroll_id
    l_results = []    
    res = qmamf(l_query_must=l_query_must,l_fields=l_fields, size=size, query_type="scan", index_name=index_name, doc_type=doc_type )
    scroll_size = res['hits']['total']
    print "[gen_qmamf_long]scroll size: %s" % scroll_size
    while (scroll_size > 0):
        try:
            #print "scroll_size: %i" % scroll_size

            # next iteration of scrolled results
            # Note that when using scan search, the first set of hits is always []
            # 60 second timeout for holding scroll results.
            l_results += res['hits']['hits']
            scroll_id = res['_scroll_id']
            res = es.scroll(scroll_id=scroll_id, scroll='60s')
            #pdb.set_trace()
            # recalculate next scroll_size based on number hits returned for next iteration
            # When it is 0, we are done with the loop.
            scroll_size = len(res['hits']['hits'])
            #print "scroll_id: %s" % scroll_id
            # return results for this iteration
            yield l_results

            l_results = []
            print "[gen_qmamf_long]num_hits: %s" % scroll_size
        except:
            print "[gen_qmamf_long] Exception when handling scroll_id."
            break

# query applying match_phrase to multiple fields (and optional filters) 
# l_filter_must is a list of field/value term restrictions on unanalyzed fields, which are
# turned into { "term": { field : value }}
# r = es_np_query.qmamf(l_query_must=[["length", 3]],l_fields=["doc_id", "phr"], size=3, query_type="scan" )

# r = es_np_query.qmamf(l_query_must=[["length", 3]],l_fields=["doc_id", "phr"], size=3, query_type="search", index_name="i_testg")
# r = es_np_query.qmamf(l_query_must=[["section", "BACKGROUND" ], ["spv", "increase"], ["sp", "cost ]"] ],l_fields=["spv", "cphr", "section"], size=3, query_type="search", index_name="i_cs_2002")

# r = es_np_query.qmamf(l_query_must=[["spv", "increase"], ["sp", "cost ]"] ],l_fields=["spv", "cphr", "section"], query_type="search", index_name="i_cs_2002")
# r = es_np_query.qmamf(l_query_must=[["spv", "increase"], ["sp", "cost ]"] ],l_fields=["spv", "cphr", "section"], query_type="search", index_name="i_bio_2002")


def qmamf(l_query_must=[], l_filter_must=[], l_fields=[], doc_type="np", index_name="i_nps_bio", query_type="search", debug_p=False, size=max_result_size):

    #pdb.set_trace()
    # fields are illegal for a count query, so ignore them
    if query_type == "count":
        l_fields = []

    l_must_query = make_must_query_phr_list(l_query_must, debug_p=debug_p)    
    l_must_filter = make_must_filter_list(l_filter_must)

    ###print "[qmaf] l_must_term: %s" % l_must_term
    queryBody = {
        
        "query": {
            "constant_score" : {
                "query" : {
                    "filtered" : {
                        "query": {
                            "bool" : {
                                "must" : l_must_query
                                }
                            },
                        "filter": {
                            "bool": {
                                "must" : l_must_filter
                                }
                            }
                        }
                    },
                # boost is a child of constant_score
                "boost" : 1.0
            }
        }
     }

    # Restrict output to named fields
    if l_fields != []:
        queryBody["fields"] = l_fields 

    if debug_p:
        print "[qmaf] queryBody: %s" % queryBody

    if query_type == "search":
        res = es.search(index=index_name, doc_type = doc_type, body=queryBody, size=size)
    elif query_type == "count":
        res = es.count(index=index_name, doc_type = doc_type, body=queryBody)
    elif query_type == "scan":
        # scan is an efficient way of doing scrolled search by turning off sorting of results.
        res = es.search(index=index_name, doc_type = doc_type, body=queryBody, scroll='60s', search_type='scan', size=size)
    return(res)

# returns parents that meet child constraints

# r = es_np_query.qpmamf(l_query_must=[["length", 3]], doc_type="doc", size=3, query_type="scan" )

# r = es_np_query.qpmamf(l_query_must=[["length", 3]], doc_type="doc", size=3, query_type="count", index_name="i_testg")
# r = es_np_query.qpmamf(l_query_must=[["length", 3]], doc_type="doc", size=3, query_type="count", index_name="i_testg")

# Make sure the index you are running against has the parent-child mapping for the requested type.
def qpmamf(l_query_must=[], l_filter_must=[], l_fields=[], doc_type="doc", child_type="np", index_name="i_nps_bio", query_type="search", debug_p=False, size=max_result_size):

    l_must_query = make_must_query_phr_list(l_query_must, debug_p=debug_p)    
    l_must_filter = make_must_filter_list(l_filter_must)

    ###print "[qmaf] l_must_term: %s" % l_must_term

    queryBody = {
        "query": {
            "bool": {
                "must": [
                    {
                        "has_child": {
                            "type": child_type,
                            "query": l_must_query
                            }
                        }
                    ]
                }
            }
        }
    

    if debug_p:
        print "[qmaf] queryBody: %s" % queryBody

    if query_type == "search":
        res = es.search(index=index_name, doc_type = doc_type, body=queryBody, size=size)
    elif query_type == "count":
        res = es.count(index=index_name, doc_type = doc_type, body=queryBody)
    elif query_type == "scan":
        res = es.search(index=index_name, doc_type = doc_type, body=queryBody, scroll='60s', search_type='scan', size=size)
    return(res)




"""
# how to deal with "read timed out" errors for long queries
# 
1.Increase the default timeout Globally when you create the ES client by passing the timeout parameter. Example in Python

es = Elasticsearch(timeout=30)

2.Set the timeout per request made by the client. Taken from Elasticsearch Python docs below.

# only wait for 1 second, regardless of the client's default
es.cluster.health(wait_for_status='yellow', request_timeout=1)

The above will give the cluster some extra time to respond
"""

# shortcut
# es_np.qcsp("abnormal cells")
# count
# es_np.qcsp("test")
def qcsp(sp_value):
    index_name = "i_nps_bio"
    r = qmaf("sp", sp_value, l_must=[], doc_type="np", index_name=index_name, query_type="count")["count"]
    return(r)

# search
# es_np.qssp("test")
def qssp(sp_value):
    index_name = "i_nps_bio"
    r = qmaf("sp", sp_value, l_must=[], doc_type="np", index_name=index_name, query_type="search")
    return(r)

# test simple phrase match
# r = es_np_query.qp("phr", "system", fields=["phr"], size=20)
# r = es_np_query.qp("phr", "human skin fibroblast cell line", fields=["phr"])
# see http://stackoverflow.com/questions/21343549/can-i-specify-the-result-fields-in-elasticsearch-query
# returns the list of hits, restricted to the fields specified.
def qp(field, value, fields=["phr"], doc_type="np", index_name="i_nps_bio", pp=True, size=max_result_size):
    #queryBody = {"query": {"match_phrase":{field : value}}}
    queryBody = {}
    if field != "":
        queryBody["query"] = {"match_phrase":{field : value}}
    if fields != []:
        queryBody["fields"] = fields 
    
    res = es.search(index=index_name, doc_type = doc_type, body=queryBody, size=size)
    if pp:
        for hit in res["hits"]["hits"]:
            print "%s" % hit["fields"]
    return(res["hits"]["hits"])

# count for multiple phrase matched fields (a query and a filter)
# uses qmamf(l_query_must=[], l_filter_must=[], doc_type="np", index_name="i_nps_bio", query_type="search")
# es_np.qc_mult([["spn", "[ skin" ], ["sp", "human ]" ]])
def qc_mult(l_query_must, l_filter_must=[], debug_p=False):
    index_name = "i_nps_bio"
    r = qmamf(l_query_must, l_filter_must, doc_type="np", index_name=index_name, query_type="count", debug_p=debug_p )["count"]
    return(r)

# es_np_query.qs_mult([["spn", "[ skin" ], ["sp", "human ]" ]])
# es_np_query.qs_mult([["phr", "human cell line" ]], l_fields=["phr", "doc_id"] )
# search for multiple phrase matched fields
def qs_mult(l_query_must, l_filter_must=[], l_fields=[], debug_p=False):
    index_name = "i_nps_bio"
    r = qmamf(l_query_must=l_query_must, l_filter_must=l_filter_must, l_fields=l_fields, doc_type="np", index_name=index_name, query_type="search", debug_p=debug_p )["hits"]["hits"]
    return(r)
    

# es_np.qbp("sp", "third | term ]", "np", "i_np")
def qbp(field, value, doc_type="tf", index_name="test1"):
    queryBody = {
       "query" : {
          "filtered" : { 
             "filter" : {
                    {"match_phrase":{field : value}}} }}}

    res = es.search(index=index_name, doc_type = doc_type, body=queryBody, size=max_result_size)
    return(res)

# constant_score prevents scoring, so saves time
# es_np.csq("sp", "third | term ]")
def csq(field, value, doc_type="np", index_name="i_np"):
    queryBody = {
        "query" : {
            "constant_score" : {
                "query" : {
                    "match_phrase" : { field : value}
                },
                "boost" : 1.0
            }
        }
     }
    res = es.search(index=index_name, doc_type = doc_type, body=queryBody, size=max_result_size)
    return(res)

# queries and filters: http://www.elasticsearch.org/guide/en/elasticsearch/guide/current/_most_important_queries_and_filters.html
# hit count within docs: https://groups.google.com/forum/#!msg/elasticsearch/vRxbDxqjxVg/AXVK6ZW_tikJ

# constant_score prevents scoring, so saves time
# filtered constrains the search
# es_np.csqf("sp", "third | term ]", year=2000)
def csqf(field, value, year=2000, doc_type="np", index_name="i_np"):
    queryBody = {
        "query" : {
            "constant_score" : {
                "query" : {
                    "filtered" : {
                        "query" : {
                            "match_phrase" : { field : value}
                            },
                        "filter" : {
                            "term" : {"year" : year }
                            }
                        }

                 },
                "boost" : 1.0
            }
        }
     }
    res = es.search(index=index_name, doc_type = doc_type, body=queryBody, size=max_result_size)
    return(res)

# constant_score prevents scoring, so saves time
# filtered constrains the search, here using a boolean expression, in which
# all exact matches ("term" matches unanalyzed fields exactly) must be satisfied.
# es_np.csqfb("sp", "third | term ]", domain="cs", year=2000, doc_id='pat2')
def csqfb(field, value, year=2000, doc_type="np", index_name="i_np", domain="cs", doc_id="pat2"):

    queryBody = {
        "query" : {
            "constant_score" : {
                "query" : {
                    "filtered" : {
                        "query" : {
                            "match_phrase" : { field : value}
                            },
                        "filter" : {
                            "bool" : { 
                                "must" : [ 
                                    {"term" : {"year" : year }},
                                    {"term" : {"domain" : domain }},
                                    {"term" : {"doc_id" : doc_id }}
                                    ]


                                }

                            }
                        }

                 },
                "boost" : 1.0
            }
        }
     }

    print "[csqfb] queryBody: %s" % queryBody

    res = es.search(index=index_name, doc_type = doc_type, body=queryBody, size=max_result_size)
    return(res)

# constant score query filtered boolean must
def csqfb_null_must(field, value, year=2000, doc_type="np", index_name="i_np", domain="cs", doc_id="pat2"):

    queryBody = {
        "query" : {
            "constant_score" : {
                "query" : {
                    "filtered" : {
                        "query" : {
                            "match_phrase" : { field : value}
                            },
                        "filter" : {
                            "bool" : { 
                                "must" : []
                                }

                            }
                        }

                 },
                "boost" : 1.0
            }
        }
     }

    print "[csqfb] queryBody: %s" % queryBody

    res = es.search(index=index_name, doc_type = doc_type, body=queryBody, size=max_result_size)
    return(res)

# boolean without scoring
# es_np.qb("0", "term", "1", "third", "np", "i_np")
def qb(f1, v1, f2, v2, doc_type="np", index_name="i_np"):

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
    
    res = es.search(index=index_name, doc_type = doc_type, body=queryBody, size=max_result_size)
    return(res)


# boolean without scoring
# es_np.qbm("sp", "[ here", "sp", "third | term ]", "np", "i_np")
# incorrect syntax ///
def qbm(f1, v1, f2, v2, doc_type="np", index_name="i_np"):

    queryBody = {
       "query" : {
          "filtered" : { 
             "filter" : {
                "bool" : {
                  "must" : [
                     { "match_phrase" : {f1 : v1}}, 
                     { "match_phrase" : {f2 : v2 }} 

                  ]

                  }
               }
             }
          }
       }
    
    res = es.search(index=index_name, doc_type = doc_type, body=queryBody, size=max_result_size)
    return(res)

# es_np.qf("phr", "third term", "np", "i_np")
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

    res = es.search(index=index_name, doc_type = doc_type, body=queryBody, size=max_result_size)
    return(res)

# l_must is a list of [field, value] pairs
def make_must_filter_list(l_must):
    l_must_term = []
    for pair in l_must:
        field = pair[0]
        value = pair[1]
        l_must_term.append({"term" : { field : value }})
    return(l_must_term)

# l_must is a list of [field, value] pairs and query type is match_phrase
# see http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/query-dsl-filtered-query.html#_multiple_filters
def make_must_query_phr_list(l_must, debug_p=False):
    if debug_p:
        print "[make_must_query_phr_list]l_must: %s" % l_must
    l_must_query = []
    for pair in l_must:
        field = pair[0]
        value = pair[1]
        l_must_query.append({"match_phrase" : { field : value }})
    if debug_p:
        print "[make_must_query_phr_list]l_must_query: %s" % l_must_query
    return(l_must_query)

# no filter terms
# es_np.qfnull("phr", "third term", "np", "i_np")
def qfnull(field, value, doc_type="tf", index_name="test1"):
    queryBody = {"query": {"filtered" : {
                             "query": { "match_all": {}},
                              
                              "filter": {}
                             }}}
    res = es.search(index=index_name, doc_type = doc_type, body=queryBody, size=max_result_size)
    return(res)

# query with only filter
def qf2(field, value, doc_type="tf", index_name="test1"):
    queryBody = {                              
                              "filter": {
                                  "bool": {
                                     "must" : {
                                        "term" : { 
                                            field : value
                                            }

                                        }}}}


    res = es.search(index=index_name, doc_type = doc_type, body=queryBody, size=max_result_size)
    return(res)

# es_np_query.docs_matching("human cell line")
# Note that we are matching individual phrases, so the same
# doc_id can match multiple times.  Hence, we use doc_set to
# remove dup docs from the result. But return a list (with no dups)
def docs_matching(phr):
    doc_set = set()
    result = qs_mult([["phr", phr ]], l_fields=["doc_id"] )
    for r in result:
        doc_set.add(r["fields"]["doc_id"][0])
    return(list(doc_set))

# given a phrase, return several measures of diversity:
# count of different governing verbs
# count of different governing Npr
# count of different mods
# count of different heads
def diversity(phr):
    # create an sp form of the phrase, to allow stemming and enforce bounds of the phrase
    sp_full = phr2sp(phr, phr_subset="f")
    sp_right = npr2spn_sp("sp", phr, phr_subset="r")
    sp_left = npr2spn_sp("sp", phr, phr_subset="l")
    
    
    d_spv2count = defaultdict(int)
    d_spn2count = defaultdict(int)
    d_mod2count = defaultdict(int)
    d_head2count = defaultdict(int)

    # fetch full matches to get the Npr and prev_V values
    res = qmamf(l_query_must=[["sp", sp_full ]],l_fields=["spv", "spn"])["hits"]["hits"]

    res_count = 0
    for result in res:
        res_count += 1
        if result.has_key("fields"):
            fields = result["fields"]

            if fields.has_key("spv"):
                d_spv2count[fields["spv"][0]] += 1
                #print "adding to %s" % d_spv2count[fields["spv"][0]] 
                #pdb.set_trace()
            if fields.has_key("spn"):
                d_spn2count[fields["spn"][0]] += 1
                #print "adding to %s" % d_spn2count[fields["spn"][0]] 

    # emit totals
    spn_len = len((d_spn2count.keys())) 
    spv_len = len((d_spv2count.keys())) 
    log_spn_len = math.log(spn_len, 2)
    log_spv_len = math.log(spv_len, 2)
    log_res_count = math.log(res_count, 2)
    spn_ratio = spn_len*1.0 / res_count
    log_spn_ratio = log_spn_len*1.0 / log_res_count
    spv_ratio = spv_len*1.0 / res_count
    log_spv_ratio = log_spv_len*1.0 / log_res_count

    print "res_count: %i" % res_count    
    print "spn: %i (%.2f) %.2f" % (spn_len, spn_ratio, log_spn_ratio)
    print "spv: %i (%.2f) %.2f" % (spv_len, spv_ratio, log_spv_ratio)

# entropy of modifiers of the phr
def mod_entropy(phr):
    # create an sp form of the phrase, to allow stemming and enforce bounds of the phrase
    sp_right = phr2sp(phr, phr_subset="r")
    
    d_mod2count = defaultdict(int)
    d_head2count = defaultdict(int)
    l_freqs = []

    phr_len = len(phr.split(" "))

    # fetch full matches to get the Npr and prev_V values

    # TBD match on canonical form, so we collapse variations into a single phrase name
    res = qmamf(l_query_must=[["sp", sp_right ]],l_fields=["phr"])["hits"]["hits"]

    # do we want to count by one-instance-per-doc or by all instances within doc
    res_count = 0
    # how often a modifier occurs with this phrase
    mod_occurrence_freq = 0
    sum_entropy = 0
    entropy = 0

    #return("done")
    for result in res:
        res_count += 1
        if result.has_key("fields"):
            fields = result["fields"]

            # only include the rightmost word of the modifier
            match = fields["phr"][0]
            l_match_words = match.split(" ")[(-1)*(phr_len+1):]
            trimmed_phr = " ".join(l_match_words)

            d_mod2count[trimmed_phr] += 1
            mod_occurrence_freq += 1
            
    if mod_occurrence_freq == 0:
        entropy = 0
        print "in if"
    else:
        for key in d_mod2count.keys():
            freq = d_mod2count[key]
            #pdb.set_trace()
    
            prob_mod =  (freq * 1.0) / mod_occurrence_freq
            l_freqs.append([key, freq])
            
            sum_entropy += prob_mod * math.log(prob_mod, 2)
            
        if sum_entropy == 0:
            entropy = 0
        else:
            entropy = (-1)*sum_entropy
    num_mods = len(l_freqs)
    l_freqs = sorted(l_freqs, key=lambda(k,v): v, reverse=True)
    print "sum_entropy: %f, #mods: %i, l_freqs: %s" % (entropy, num_mods, l_freqs[0:10])
    return(entropy)

    # we compute entropy as prob of the (mod | head) where phr is the head
    # H(mod) = - sum (prob (mod) * log2 prob(mod) )
    # we need the total number of mod occurrences
    # and the freq for each mod

# find the most freq features in a given list of phrases
def freq_features(l_phr):
    d_spv2count = defaultdict(int)
    d_spn2count = defaultdict(int)


    instance_count = 0

    for phr in l_phr:
        # create an sp form of the phrase, to allow stemming and enforce bounds of the phrase
        sp_full = phr2sp(phr, phr_subset="f")

        # fetch full matches to get the Npr and prev_V values
        res = qmamf(l_query_must=[["sp", sp_full ]],l_fields=["spv", "spn"])["hits"]["hits"]

        # sets of features encountered for this phrase
        l_spv_feats = set()
        l_spn_feats = set()

        for result in res:
            instance_count += 1
            if result.has_key("fields"):
                fields = result["fields"]

                if fields.has_key("spv"):
                    # we need to convert the list into a tuple to add to a set
                    l_spv_feats.add(tuple(fields["spv"]))


                if fields.has_key("spn"):
                    l_spn_feats.add(tuple(fields["spn"]))

        for spv_feat in l_spv_feats:
            # increment the count for this feature for this phrase
            d_spv2count[spv_feat] += 1
        for spn_feat in l_spn_feats:
            d_spn2count[spn_feat] += 1
    # now sort the features by freq of occurrence with these phrases
    l_spv = sorted(d_spv2count.items(), key=lambda (k, v): v)
    l_spn = sorted(d_spn2count.items(), key=lambda (k, v): v)
    print "spv: %s\n" % l_spv
    print "spv: %s\n" % l_spn

# related terms using sterms in sent doc_type
# es_np_query.related("airline ticket", "i_cs_2002", size=200)
# If multiword == True, only output phrases containing > 1 word.
def related(phr, index_name, size=2000,  multiword_p=True, max=20):
    l_phr = phr.split(" ")
    term = "_".join(l_phr)
    l_query_must = [["sterm", term] ]
    l_fields=[ "sterms", "section"]
    l_hits = qmamf_long(l_query_must=l_query_must, l_filter_must=[], l_fields=l_fields, doc_type="sent", index_name=index_name, size=size, debug_p=False)

    #l_hits = res["hits"]["hits"]

    d_rel2freq = defaultdict(int)
    for hit in l_hits:
        for term in hit["fields"]["sterms"]:
            d_rel2freq[term] += 1
    # sort dictionary keys by value
    sorted_terms = sorted(d_rel2freq.items(), key=operator.itemgetter(1), reverse=True)
    #pdb.set_trace()
    i = 1
    for item in sorted_terms:
        
        if (not multiword_p) or ("_" in item[0]):
        #
            print "%s:%i" % item
            if i > max:
                break
            i += 1

#es_np_query.doc_freq("airline ticket", "i_cs_2002")
def doc_freq(phr, index_name, phr_subset="f"):
    value = phr2sp(phr, phr_subset="f")
    query_must = [ "sp", value ]
    res = qpmamf(l_query_must=[query_must], doc_type="doc", child_type="np", index_name=index_name, query_type="count", debug_p=False)

    query_must_cphr = ["cphr", phr]
    cphr_res = qpmamf(l_query_must=[query_must_cphr], doc_type="doc", child_type="np", index_name=index_name, query_type="count", debug_p=False)

    query_must_phr = ["phr", phr]
    phr_res = qpmamf(l_query_must=[query_must_phr], doc_type="doc", child_type="np", index_name=index_name, query_type="count", debug_p=False)

    return([res, cphr_res, phr_res])

# es_np_query.dump_ngrams("i_bio_2003", 2, "bio.2003.2.inst")
def dump_ngrams(index_name, ngram_length, output_file):
    res_generator = gen_qmamf_long(l_query_must=[["length", ngram_length]],l_fields=["doc_id", "phr", "cphr"], size=500, index_name="i_bio_2003")
    dump_gen_rfields(res_generator, l_fieldnames=["cphr", "phr", "doc_id"], l_fieldtypes=["s", "s", "s"], output_file=output_file)
    
