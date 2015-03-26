# es_np.py
# elasticsearch indexing of np chunks
# PGA 1/17/15
# see http://exploringelasticsearch.com/searching_data.html for examples


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

# general es utils

def refresh_index(index_name):
    #important! refresh index after loading
    es.indices.refresh(index=index_name)

# meta for bulk_loading
def format_d_action(index_name, type_name, uid):
    d_action = { "index":{"_index": index_name ,"_type": type_name, "_id": uid }} 
    return(d_action)

# mapping and index creation

# patterns for matching specific features in a phr_feats line
# doc_loc value is the sentence number in the patent, starting at 0
p_doc_loc = re.compile('doc_loc=([^\s]*)' )
p_prev_V = re.compile('prev_V=([^\s]*)' )
p_prev_J = re.compile('prev_J=([^\s]*)' )
p_prev_Npr = re.compile('prev_Npr=([^\s]*)' )


# for mapping examples, see http://exploringelasticsearch.com/searching_usernames_and_tokenish_text.html 
def create_np_index(index_name):
    d_np_schema = {
        "settings": {
            "analysis": {
                "filter": {
                    # use the porter stemmer for verbs
                    "stemmer_eng_v": {
                        "type": "stemmer",
                        "name": "porter2" },
                    # use the minimal stemmer for plural nouns
                    "stemmer_eng_n": {
                        "type": "stemmer",
                        "name": "minimal_english" 
                        #"name": "light_english" 
                        #"name": "porter2" 
                        }
                    },
                        
                # we want our analyzers to preserve punctuation, which we use as 
                # term boundary markers in some fields ([|])
                # phrase fields are pre-tokenized using whitespace as separator, so we don't 
                # need to do any fancier tokenization in elasticsearch.
                
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

        # "np" here is the type of object to be indexed
        # for index options, see http://www.elasticsearch.org/guide/en/elasticsearch/guide/current/stopwords-phrases.html#index-options
        
        # only the s* fields are subjected to stemming.
        "mappings":{
            "np": {"properties":
                       # term is the NP as a single token with "_" separating words
                   {"term":{"type":"string", "index": "not_analyzed"  , "index_options": "docs"},
                    # phr is NP with whitespace separating words
                    "phr":{"type":"string","analyzer":"analyzer_whitespace","index_options":"offsets"},
                    # sp is NP with | separating words and start and end brackets ([])
                    "sp":{"type":"string","analyzer":"analyzer_eng_n","index_options":"offsets"},
                    # syntactic relations
                    "prev_Npr":{"type":"string","index":"not_analyzed","index_options":"docs"},
                    "spn":{"type":"string","analyzer":"analyzer_eng_n","index_options":"offsets"},
                    "prev_V":{"type":"string","index":"not_analyzed","index_options":"docs"},
                    "spv":{"type":"string","analyzer":"analyzer_eng_v","index_options":"offsets"},
                    "prev_J":{"type":"string","index":"not_analyzed","index_options":"docs"},
                    # components of the NP
                    "head":{"type":"string","index":"not_analyzed","index_options":"docs"},
                    # meta info
                    "domain":{"type":"string","index":"not_analyzed", "index_options":"docs"},
                    "year":{"type":"integer","index": "not_analyzed", "index_options":"docs"},
                    "doc_id":{"type":"string","index":"not_analyzed", "index_options":"docs"},
                    "loc":{"type":"integer","index": "not_analyzed", "index_options":"docs"},
                    "length":{"type":"integer","index": "not_analyzed", "index_options":"docs"},
                    
                    }}}}
    
    np_index = es.indices.create(index=index_name, body=d_np_schema)
    return(d_np_schema)

# index population

# create a dictionary that matches the schema 

# Given a phrase with separator char = split_char,
# create a bracketed phrase with "|" as internal separator
# e.g., "web server software" => "[ web | server | software ]"
def make_separated_phrase(phrase, split_char=" "):
    sp = phrase.replace(split_char, " | ")
    sp = "[ " + sp + " ]"
    return(sp)

# create a dictionary that matches the schema 
def format_np_d_content(phr, prev_Npr, prev_V, prev_J, domain, year, doc_id, loc):
    d_content = {"phr": phr, 'domain': domain, 'year': year, 'doc_id': doc_id, 'loc': loc}
    # add the remaining fields (if they exist)
    # length = number of tokens in the phrase
    l_tokens = phr.split(" ")
    d_content["length"] = len(l_tokens)
    term = phr.replace(" ", "_")
    sp = make_separated_phrase(phr, split_char=" ")

    d_content["sp"] = sp
    d_content["term"] = term
    d_content["head"] = term.split("_")[-1]
    if prev_Npr != None:
        d_content["prev_Npr"] = prev_Npr
        spn = make_separated_phrase(prev_Npr, split_char="_")
        d_content["spn"] = spn
    if prev_V != None:
        d_content["prev_V"] = prev_V
        spv = make_separated_phrase(prev_V, split_char="_")
        d_content["spv"] = spv
    if prev_J != None:
        d_content["prev_J"] = prev_J

    return(d_content)

# make bulk loading list for test2 db
def test2_make_bulk():
    index_name = "test2"
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
        l_bulk_elements.append(format_d_action(index_name, type_name, uid))
        l_bulk_elements.append(format_np_d_content(term, prev_Npr, prev_V, prev_J, domain, year, doc_id, loc))

        i += 1    
    
    return(l_bulk_elements)

#es_np.test2_populate()
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
                if not(section_filter_p) or line.find("TITLE") > 0 or line.find("ABSTRACT") > 0 or line.find("SUMMARY") > 0:
                    # then process the line
                    l_data = line.split("\t")
                    # chunk is phrase with  blanks connecting tokens
                    uid = l_data[0]  # uid is doc_id + phrase number
                    phr = l_data[2]  # phrase with whitespace separating words

                    # extract the value field from the doc_loc feature to get the loc (sentence number)
                    loc = p_doc_loc.search(line).group(1)
                    # We will store it as an integer in es
                    loc = int(loc)

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
                    l_bulk_elements.append(format_d_action(index_name, type_name, uid))
                    l_bulk_elements.append(format_np_d_content(phr, prev_Npr, prev_V, prev_J, domain, year, patent_id, loc))

                    num_lines_output += 1
       

                # stop after max_lines files for debugging
                ###print "num_lines_output: %i, max_lines: %i" % (num_lines_output, max_lines)
                if (max_lines != 0) and num_lines_output > max_lines: 
                    break
            # break out of file loop as well
            if (max_lines != 0) and num_lines_output > max_lines: 
                break

            s_phr_feats.close()            

        s_json.close()

    log_message = "[es_np.py]Completed make_bulk_lists for years: " + str(start) + " " + str(end) + ". Number of lines: " + str(num_lines_output)
    time = log.log_current_time(s_log, log_message, True)

    s_log.close()
    s_file_list.close()

    # yield the last remainingl_bulk_elements

    print "[gen_bulk_lists]%i lines from %i files written to index %s" % (num_lines_output, file_count, index_name)
    yield(l_bulk_elements)

# Lists are too long to process as a single list. Use generator to mix bulk list creation and indexing
# got timeout error withe docs_per_bulk_load=500
# es_np.np_populate("i_np", "computers", "ln-us-A21-computers", 1997, 1997, 100, True, True, 3)
# es_np.np_populate("i_np_bio", "biology", "ln-us-A27-molecular-biology", 2003, 2003, 5000, True, True, 0)
# es_np.np_populate("i_testg", "biology", "ln-us-A27-molecular-biology", 2003, 2003, 2, True, True, 9)

# i_nps is np index with stemming applied to the sp* fields
# es_np.np_populate("i_nps_bio", "biology", "ln-us-A27-molecular-biology", 2003, 2003, 50000, True, True, 0)
# The raw data is located here: 
# /home/j/anick/patent-classifier/ontology/roles/data/patents/ln-us-A27-molecular-biology/data/term_features/2003
# Number of patents in year 2003: 38343
def np_populate(index_name, domain, corpus, start_year, end_year, lines_per_bulk_load=5000, section_filter_p=True, new_index_p=True, max_lines=0):

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
        print "[es_np.py] created np index: %s" % index_name

    # now bulk load data
    # first create the list of elements for bulk loading
    bulk_generator = gen_bulk_lists(index_name, type_name, domain, corpus, start_year, end_year, lines_per_bulk_load, section_filter_p=True, max_lines=max_lines)
    ###pdb.set_trace()
    print "[es_np.py] created data generator for bulk loading"
    ### print "[es_np.py] l_bulk_lists: %s" % (l_bulk_lists)

    # Now load each sublist of elements into elasticsearch
    num_sublists = 0
    for l_bulk_elements in bulk_generator:
        num_sublists += 1
        res = es.bulk(l_bulk_elements)
        print "[es_np.py] Bulk loaded sublist %i" % num_sublists
    print "[es_np.py] bulk loading completed"

    # and refresh the index
    refresh_index(index_name)
    print "[es_np.py] index refreshed"

