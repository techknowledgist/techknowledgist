# es_np.py
# elasticsearch indexing of np chunks
# PGA 1/17/15

# NOTE: As of 3/8/2015, this file has been broken up into 
# es_np_index.py
# es_np_query.py
# es_np_nc.py

# This file should no longer be used!!

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
                    # sphr is NP with | separating words and start and end brackets ([])
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

                    # extract the value field from the doc_loc feature to get the lo (sentence number)
                    loc = p_doc_loc.search(line).group(1)

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



# pmi is standard pmi
# norm_pmi is standard pmi normalized by the log of the pair_prob
# fpmi multiplies by the log of the joint frequency to boost scores of
# more frequent combinations.
def pmi(term1, freq1, term2, freq2, joint_freq, n, pmi_type="pmi"):

    # default value in case the pmi cannot be computed due to 0 freq somewhere
    pmi = -1000
    mi = -1000
    norm_pmi = -1000  
    fpmi = -1000

    term1_prob = float(freq1)/n
    term2_prob = float(freq2)/n

    pair_prob = float(joint_freq)/n
    # compute normalized pmi
    # Check for odd cases where a term prob of 0 arises
    # It shouldn't happen but it does
    denom = term1_prob * term2_prob
    
    if denom == 0:
        if verbose_p:
            print "0 probability for term1: [%s, %f] or term2: [%s, %s]" % (term1, term1_prob, term2, term2_prob)
        pass
    elif pair_prob == 0:
        if verbose_p:
            print "0 probability for pair: %s, %s" % (term1, term2)
        pass
    else:
        pmi = math.log(pair_prob/(term1_prob * term2_prob),2)
        mi = pair_prob * pmi
        norm_pmi = pmi / (-1 * math.log(pair_prob, 2))

        # compute npmi * log(freq)
        fpmi = norm_pmi * math.log(joint_freq, 2)
        if verbose_p:
            print "[pmi]npmi/fpmi for %s %s: %f, %f  freq/probs: %i/%f, %i/%f, %i/%f" % (term1, term2, norm_pmi, fpmi, freq1, term1_prob, freq2, term2_prob, joint_freq, pair_prob)
    #s_outfile.write( "%st%st%ft%ft%it%it%i\n" % (term1, term2, fpmi, norm_pmi, d_pair_freq[pair], d_term_freq[term1], d_verb_freq[term2]))
    if pmi_type == "pmi":
        result = pmi
    elif pmi_type == "mi":
        result = mi
    elif pmi_type == "norm_pmi":
        result = norm_pmi
    elif pmi_type == "fpmi":
        result = fpmi
    return(result)

# TBD add in morphology on head term (pluralization)
# TBD handle 0 prob and negative probs better.
# es_np.trigram_pmi("abnormal cell proliferation")
def trigram_pmi(phr, n=39392738, index_name="i_np_bio", pmi_type="pmi"):
    l_phr = phr.split(" ")
    term_0 = l_phr[0]
    term_1 = l_phr[1]
    term_2 = l_phr[2]

    sp1 = "[ " + l_phr[0] + " | " + l_phr[1] + " ]"
    sp2 = "[ " + l_phr[1] + " | " + l_phr[2] + " ]"
    sp3 = "[ " + l_phr[0] + " | " + l_phr[2] + " ]"
    
    joint_freq_0_1 = qmaf("sp", sp1, l_must=[], doc_type="np", index_name=index_name, query_type="count")["count"]
    joint_freq_1_2 = qmaf("sp", sp2, l_must=[], doc_type="np", index_name=index_name, query_type="count")["count"]
    joint_freq_0_2 = qmaf("sp", sp3, l_must=[], doc_type="np", index_name=index_name, query_type="count")["count"]
    freq_0 = qmaf("sp", l_phr[0], l_must=[], doc_type="np", index_name=index_name, query_type="count")["count"]
    freq_1 = qmaf("sp", l_phr[1], l_must=[], doc_type="np", index_name=index_name, query_type="count")["count"]
    freq_2 = qmaf("sp", l_phr[2], l_must=[], doc_type="np", index_name=index_name, query_type="count")["count"]

    pmi_ab = pmi(term_0, freq_0, term_1, freq_1, joint_freq_0_1, n, pmi_type=pmi_type)
    pmi_bc = pmi(term_1, freq_1, term_2, freq_2, joint_freq_1_2, n, pmi_type=pmi_type)
    pmi_ac = pmi(term_0, freq_0, term_2, freq_2, joint_freq_0_2, n, pmi_type=pmi_type)

    # adjacency measure
    score1 = pmi_bc - pmi_ab
    # dependency measure of first term to potential head terms
    score2 = pmi_ac - pmi_ab

    # simple combination score (with equal weighting)
    score3 = score1 + score2

    brackets = []
    if score1 > 0:
        brackets.append("r")
    else:
        brackets.append("l")

    if score2 > 0:
        brackets.append("r")
    else:
        brackets.append("l")

    if score3 > 0:
        brackets.append("r")
    else:
        brackets.append("l")

    return(brackets)


def vote_max(label_list):
    return max(set(label_list), key=label_list.count)


def bracket_trigram(trigram, label):
    l_words = trigram.split(" ")
    if label == "l":
        br = [ [ l_words[0], l_words[1] ], l_words[2] ]
    else:
        br = [ l_words[0], [l_words[1], l_words[2] ] ]
    return(br)

# evaluate trigram gold data using the bracketing output from bracket() as well as pmi values
# filter="all" to include all phrases in eval
# filter="corpus" to include only phrases that appear as a whole in the corpus
# es_np.eval_bio_br("bio_trigrams.dat", "bio_trigrams_br.eval", pmi_type="pmi", filter="all", score_method="full_adj")  
def eval_bio_br(gold_file, eval_file, pmi_type="pmi", filter="all", score_method="full_adj"):
    s_infile = codecs.open(gold_file, encoding='utf-8')
    s_eval_file = codecs.open(eval_file, "w", encoding='utf-8')

    phrase_count = 0
    # phrases that occur at least once in corpus 
    phrase_corpus_count = 0
    match1_count = 0
    match2_count = 0
    match3_count = 0
    match4_count = 0
    match5_count = 0

    label_letters = ["l", "r"]

    line_count = 0
    for line in s_infile:
        line_count += 1
        """
        # for debugging, stop after a few lines
        if line_count > 3:
            break
        """

        line = line.strip()
        [gold_label, phrase] = line.split("\t")
        # replace the letter label with the equivalent l or r bracketed phrase
        gold_label_br = bracket_trigram(phrase, gold_label)
        # let system_label_br be the top ranked bracketing for the phrase
        # NOTE: need to deal with ties.  Right now we simply take the first in the list. ///
        #system_label_br = bracket(phrase)[0][2]

        # use the br methods rather than bracket()
        br1 = br(phrase, es)
        #br1.tree_counts()

        l_score_info = br1.d_method2sorted_scores[score_method]
        # get the bracketing of the top ranked score
        system_label_br = l_score_info[0][2]
        if verbose_p:
            print "system_label_br: %s " % (system_label_br)

        phrase_count += 1

        #print "%s" % phrase
        label_list = trigram_pmi(phrase, n=39392738, index_name="i_nps_bio", pmi_type="pmi")
        [l1, l2, l3] = label_list
        
        # set l5 to be the label (l,r) the system chooses, based on comparing the bracketed formats
        # ie. we are translating from bracketings to (l,r) assuming that since there are only two choices,
        # then if system and gold agree, use the gold label, if not, use the complementary label.
        ###pdb.set_trace()
        if gold_label_br == system_label_br:
            l5 = gold_label
        else:
            # l5 gets the opposite label

            label_letters_copy = list(label_letters)
            label_letters_copy.remove(gold_label)
            
            l5 = label_letters_copy[0]
            #/// bug - the match always fails.
            print "setting l5 to %s, opposite of gold_label: %s" % (l5, gold_label)
            #pdb.set_trace()
        # vote for the highest freq label from the 3 MI metrics
        vote_label = vote_max(label_list)

        print "gold: %s %s (vl,l1,l2,l3,l5:) %s %s %s %s %s\t%s" % (gold_label_br, gold_label, vote_label, l1, l2, l3, l5, phrase)
        #pdb.set_trace()
        
        # check if the phrase occurs in the corpus
        corpus_count = qmaf("phr", phrase, index_name="i_nps_bio", query_type="count")["count"]

        if filter == "corpus":
            if corpus_count > 0:
                if gold_label == l1:
                    match1_count += 1

                if gold_label == l2:
                    match2_count += 1

                if gold_label == l3:
                    match3_count += 1

                if gold_label == vote_label:
                    match4_count += 1

                if gold_label_br == system_label_br:
                    match5_count += 1

                phrase_corpus_count += 1

        elif filter == "all":
            if gold_label == l1:
                match1_count += 1

            if gold_label == l2:
                match2_count += 1

            if gold_label == l3:
                match3_count += 1

            if gold_label == vote_label:
                match4_count += 1

            if gold_label_br == system_label_br:
                match5_count += 1

            phrase_corpus_count += 1

    print "matches: %i, %f, %i, %f, %i, %f, %i, %f, %i, %f out of %i (total: %i)" % (match1_count, float(match1_count)/phrase_corpus_count, match2_count, float(match2_count)/phrase_corpus_count, match3_count, float(match3_count)/phrase_corpus_count, match4_count, float(match4_count)/phrase_corpus_count, match5_count, float(match5_count)/phrase_corpus_count, phrase_corpus_count, phrase_count)

# Given a phrase, find the counts for each term to appear as the head of an Npr with the other 
# term as the object.
# eg. for stem cell research
# prev_N = research, sp = cell
# es_np.head_mod_pairs("stem cell research")
# [['research', 'cell', 2, 1], ['research', 'stem', 2, 0], ['cell', 'stem', 1, 0]]

def head_mod_pairs(phrase):
    l_words = phrase.split(" ")
    l_hm_pairs = []
    last_head_index = len(l_words) - 1
  
    # descend from last head term to first 
    # note that range does not include the last value, so the second
    # parameter is 1 index lower.
    for h in range(last_head_index, 0, -1):
        for m in range(h - 1, -1, -1):
            l_hm_pairs.append([l_words[h], l_words[m], h, m])

    return(l_hm_pairs)

def head2spn(word):
    spn_first_word_pattern = "[ " + word
    return(["spn", spn_first_word_pattern])

def mod2sp(word):
    sp_last_word_pattern = word + " ]"
    return(["sp", sp_last_word_pattern])

# not used
# es_np.count_hm_pairs("human stem cells")
def count_hm_pairs(phrase):
    l_hm_pairs = head_mod_pairs(phrase)
    l_hm_w_counts = []
    for hm_pair in l_hm_pairs:
        head = hm_pair[0]
        mod = hm_pair[1]
        # e.g. for the phrase "human skin", human is mod and skin is head
        #
        # qc_mult([["spn", "[ skin" ], ["sp", "human ]"]])
        count = qc_mult([head2spn(head), mod2sp(mod)], debug_p=True)
        # add count value to end of hm_pair vector
        hm_pair.append(count)
        l_hm_w_counts.append(hm_pair)
        print "hm_pair: %s" % hm_pair
    return(l_hm_w_counts)


##############################
# analyzing trees and scoring

class treeInfo():
    def __init__(self, num_tree, phrase, l_pairInfo):
        self.num_tree = num_tree
        self.word_tree = ntree2words(num_tree, phrase)
        self.l_pairInfo = l_pairInfo

# methods for bracketing and scoring
# b = es_np.br("human cell line", es_np.es)
class br():
    def __init__(self, phrase, es):
        self.phrase = phrase
        l_words = phrase.split(" ")
        self.d_idx2word = {}
        # elasticsearch object
        self.es = es
        # map from pair of phrase indices (e.g. (0, 2) to the counts object
        # for the mod and head at those phrase positions.  This is 
        # essentially a cache of elasticsearch count query results, since 
        # many trees will contain the same pairs
        self.d_numpair2counts = {}
        self.d_method2sorted_scores = {}
        self.l_treeInfo = []

        # map word position in phrase to word
        for idx in range(0, len(l_words)):
            self.d_idx2word[idx] = l_words[idx]

        self.tree_counts()
        self.d_method2sorted_scores["Npr"] = self.sort_scores("Npr")
        self.d_method2sorted_scores["full_adj"] = self.sort_scores("full_adj")
        self.d_method2sorted_scores["partial_adj"] = self.sort_scores("partial_adj")

        #pdb.set_trace()

    def tree_counts(self):
        phrase = self.phrase
        trees = make_br_trees_num(phrase)
        cinfo = None
        for num_tree in trees:
            # accumulate count info for all pairs in the tree

            # score the tree using es counts
            # First generate all the pairs (of mod and head terms)
            l_pairs = tree2pairs(num_tree)
            l_pairInfo = []

            for pair in l_pairs:
                loc1 = pair[0]
                loc2 = pair[1]
                w1 = self.d_idx2word[loc1]
                w2 = self.d_idx2word[loc2]
                pair_key = tuple(pair)
                if self.d_numpair2counts.has_key(pair_key):
                    # use cached data
                    pinfo = self.d_numpair2counts[pair_key]
                    #pdb.set_trace()
                else:
                    # compute counts using es and update cache
                    pinfo = pairInfo(w1, w2, loc1, loc2, self.es)
                    self.d_numpair2counts[pair_key] = pinfo
                # add the pair info for the pair to our list
                l_pairInfo.append(pinfo)
            # dump the data into a tree_info object
            ti = treeInfo(num_tree, phrase, l_pairInfo)
            self.l_treeInfo.append(ti)


        """
        for ti in self.l_treeInfo:
            self.score_pairs(ti, self.d_numpair2counts, "Npr")
            self.score_pairs(ti, self.d_numpair2counts, "full_adj")
            self.score_pairs(ti, self.d_numpair2counts, "partial_adj")

        """

    def score_pairs(self, ti, d_numpair2counts, score_method):
        #pdb.set_trace()
        # note that score_method and count_method could be different!
        # keep cumulative scores indexed by method
        # for multi, we do +1 smoothing to avoid multiplying by 0
        d_add_method2score = defaultdict(lambda:0)
        d_mult_method2score = defaultdict(lambda:1)
        l_mh_info = []
        for pi in ti.l_pairInfo:

            #print "pi: %s, ti.l_pairInfo: %s" % (pi, ti.l_pairInfo)
            #pdb.set_trace()
            # keep track of mod head and count info
            mh_info = [pi.pair]

            if score_method == "Npr":
                # Given a mod and head in the NP order ("stem cells"), we compute the number of docs
                # spn is stemmed prev_Npr  "[ cells of "  as in "cells of human stem"
                # sp is stemmed NP "stem ]"  as last word in the phrase
                # we need to compute the count using elasticsearch query qc_mult
                
                # if mod and head are adjacent, include the Npr paraphrase counts in calculation
                count = pi.d_method2count["partial_adj"]
                mh_info.append(count)
                if pi.loc2 - pi.loc1 == 1:
                    mh_info.append(pi.d_method2count["Npr"])
                    count = count + pi.d_method2count["Npr"]
                    
                d_add_method2score[score_method] = d_add_method2score[score_method] + count
                # use +1 smoothing on the multiplication scoring to avoid multiplying by 0
                d_mult_method2score[score_method] = d_mult_method2score[score_method] * (count + 1) 
                ###pdb.set_trace()
            elif score_method == "full_adj":
                
                # full adjacent (stemmed) phrase made up of the two terms
                count = pi.d_method2count["full_adj"]
                mh_info.append(count)
                d_add_method2score[score_method] = d_add_method2score[score_method] + pi.d_method2count["full_adj"] 
                d_mult_method2score[score_method] = d_mult_method2score[score_method] * (pi.d_method2count["full_adj"] + 1 ) 

            elif score_method == "partial_adj":
                # partial adjacent (stemmed) phrase made up of the two terms
                count = pi.d_method2count["partial_adj"]
                mh_info.append(count)
                d_add_method2score[score_method] = d_add_method2score[score_method] + pi.d_method2count["partial_adj"] 
                d_mult_method2score[score_method] = d_mult_method2score[score_method] * (pi.d_method2count["partial_adj"] + 1)
            l_mh_info.append(mh_info)
        #print "bracketing: %s, %s, scores(mult, add): %i\t%i" % (ti.word_tree, l_mh_info, d_mult_method2score[score_method], d_add_method2score[score_method]) 
        #print "Returning from score_pairs!"
        return([d_mult_method2score[score_method], d_add_method2score[score_method], ti.word_tree, l_mh_info])
    
    def sort_scores(self, method, debug_p=False):
        #pdb.set_trace()
        l_scores = []
        sorted_scores = []
        #pdb.set_trace()
        #print "bracketing sorted by method: %s" % method
        #pdb.set_trace()
        for ti in self.l_treeInfo:

            l_scores.append(self.score_pairs(ti, self.d_numpair2counts, method))
        sorted_scores = reversed(sorted(l_scores))
        """
        l_scores = []
        for score in sorted_scores:
            (score_mult, score_add, tree, mh_path) = score
            if debug_p:
                print "bracketing: %s %i %i %s" % (tree, score_mult, score_add, mh_path)
            l_scores.append(score)
        """
        return(l_scores)

# generate all bracketed trees for a given phrase
# use numeric indices for each word (0 - len(phrase)-1 )
# uses merge_level()
def make_br_trees_num(phrase):

    l_words = phrase.split(" ")
    # create initial list of numeric indices into the phrase (first word index = 0)
    # generate all integers from 0 to length of phrase -1 
    # create a list of leaf nodes with these numeric values
    l_leaves = range(0, len(phrase.split(" ")))
    # list of final trees
    l_final_trees = []
    partial_tree_queue = [l_leaves]
    new_partial_tree_queue = []

    # if a list in the queue has length 1, we move it to l_trees
    while len(partial_tree_queue) > 0:
        for partial_tree in partial_tree_queue:
            pt_len = len(partial_tree)
            for idx in range(0, pt_len - 1):
                merged_tree = merge_level(partial_tree, idx)
                #print "[make_trees]idx: %i, partial_tree: %s, merged_tree: %s" % (idx, partial_tree, merged_tree)
                if len(merged_tree) > 1:
                    new_partial_tree_queue.append(merged_tree)
                else:
                    # we are at root of full tree.  Place it into list of final trees.
                    # unless it is a duplicate tree
                    #pdb.set_trace()
                    if merged_tree[0] not in l_final_trees:
                        l_final_trees.append(merged_tree[0])
                #print "[make_br_trees]new_partial_tree_queue: %s" % new_partial_tree_queue
        partial_tree_queue = new_partial_tree_queue
        new_partial_tree_queue = []

    #print "[make_br_trees]l_final_trees: %s" % l_final_trees

    return(l_final_trees)


def merge_level(partial_tree, idx):
    l_new_ptree = []
    mod = idx
    head = idx + 1
    l_new_ptree = []
    #print "[Entered merge_level] partial_tree: %s len: %i" % (partial_tree, len(partial_tree))
    if len(partial_tree) == 1:
        #print "[merge_level] len(partial_tree): %i" % len(partial_tree)
        l_new_ptree = partial_tree[0]
    else:
        for npt_idx in range(0, len(partial_tree)):
            if (npt_idx < mod ) or (npt_idx > head):
                l_new_ptree.append(partial_tree[npt_idx])
            elif npt_idx == mod:
                mh = [partial_tree[mod], partial_tree[head]]
                l_new_ptree.append(mh)
    #print "[merge_level]npt_idx: %i, l_new_ptree: %s" % (npt_idx, l_new_ptree)
    return(l_new_ptree)


# generate all bracketed trees for a given phrase
# creates trees as lists of lists rather than nodes
def make_br_trees_words(phrase):
    l_words = phrase.split(" ")
    # create initial list of numeric indices into the phrase (first word index = 0)
    # generate all integers from 0 to length of phrase -1 
    l_leaves = l_words
    # list of final trees
    l_final_trees = []
    partial_tree_queue = [l_leaves]
    new_partial_tree_queue = []

    # if a list in the queue has length 1, we move it to l_trees
    while len(partial_tree_queue) > 0:
        for partial_tree in partial_tree_queue:
            pt_len = len(partial_tree)
            for idx in range(0, pt_len - 1):
                merged_tree = merge_level(partial_tree, idx)
                #print "[make_trees]idx: %i, partial_tree: %s, merged_tree: %s" % (idx, partial_tree, merged_tree)
                if len(merged_tree) > 1:
                    new_partial_tree_queue.append(merged_tree)
                else:
                    # we are at root of full tree.  Place it into list of final trees.
                    # unless it is a duplicate tree
                    if merged_tree not in l_final_trees:
                        l_final_trees.append(merged_tree[0])
                #print "[make_br_trees]new_partial_tree_queue: %s" % new_partial_tree_queue
        partial_tree_queue = new_partial_tree_queue
        new_partial_tree_queue = []

    #print "[make_br_trees]l_final_trees: %s" % l_final_trees
    return(l_final_trees)

# convert a tree to pairs of [mod, head] 
# es_np.tree2pairs(['one', ['two', 'three']])
def tree2pairs(tree):
    l_pairs = []
    def tree2pairs(tree):
        left = tree[0]
        right = tree[1]

        if isinstance(left, list):
            (lhead) = tree2pairs(left)
        else:
            lhead = left
        if isinstance(right, list):
            (rhead) = tree2pairs(right)
        else:
            rhead = right
        l_pairs.append([lhead, rhead])
        return(rhead)

    tree2pairs(tree)
    return(l_pairs)

# convert a numeric tree (containing index ordinals) to a tree containing words from the phrase
def ntree2words(tree, phrase):
    l_words = phrase.split(" ")
    key = 0
    d_num2word = {}
    # map ordinal index to word in phrase
    for word in l_words:
        d_num2word[key] = word
        key += 1

    def tree2words(tree):
        left = tree[0]
        right = tree[1]

        if isinstance(left, list):
            left = tree2words(left)
        else:
            left = d_num2word[left]
        if isinstance(right, list):
            right = tree2words(right)
        else:
            right = d_num2word[right]
        return([left, right])

    return(tree2words(tree))

# bracket a 3-word phrase using a specific relation-type as count data.
# es_np.bracket("cell membrane research paper")
def bracket(phrase, relation_type="Npr"):
    d_mh = {}
    l_scores = []
    l_trees = make_br_trees(phrase)

    for tree in l_trees:
        l_pairs = tree2pairs(tree)
        l_scores.append(score_word_pairs(l_pairs, d_mh, tree, relation_type))
    sorted_scores = reversed(sorted(l_scores))
    l_scores = []
    for score in sorted_scores:
        (score_mult, score_add, tree, mh_path) = score
        l_scores.append(score)
        print "bracketing: %s %i %i %s" % (tree, score_mult, score_add, mh_path)
    return(l_scores)

def brackets(phrase):
    for relation_type in ["Npr", "fadj"]:
        print "Relation_type: %s" % relation_type
        bracket(phrase, relation_type)

# c = es_np.pairInfo("cell", "line", 0, 1, es_np.es)
class pairInfo():
    def __init__(self, w1, w2, loc1, loc2, es):
        self.w1 = w1
        self.w2 = w2
        # to use pair as a key, make it a tuple (immutable)
        self.pair = tuple([w1, w2])
        self.loc1 = loc1
        self.loc2 = loc2
        self.Npr = 0  # w2 prep w1
        self.full_adj = 0 # [ w1 | w2 ]
        self.partial_adj = 0  # w1 | w2
        self.d_method2count = defaultdict(int)

        self.d_method2count["Npr"] = self.count_Npr(w1, w2)
        self.d_method2count["full_adj"] = self.count_full_adj(w1, w2)
        self.d_method2count["partial_adj"] = self.count_partial_adj(w1, w2)
        
    def count_Npr(self, mod, head): 
        # Given a mod and head in the NP order ("stem cells"), we compute the number of docs
        # spn is stemmed prev_Npr  "[ cells of "  as in "cells of human stem"
        # sp is stemmed NP "stem ]"  as last word in the phrase
        # we need to compute the count using elasticsearch query qc_mult
        count = qc_mult([head2spn(head), mod2sp(mod)], debug_p=False)
        return(count)

    def count_full_adj(self, mod, head):
        # full adjacent (stemmed) phrase made up entirely of the two terms
        count = qc_mult([["sp",  "[ " + mod + " | " + head + "  ]"]])
        return(count)

    def count_partial_adj(self, mod, head):
        # partial adjacent (stemmed) phrase made up of the two terms,
        # possibly within a longer phrase
        count = qc_mult([["sp",  mod + " | " + head ]])
        return(count)


# ie. based on count of spn, sp cooccurrence
def score_word_pairs(l_pairs, d_mh2counts, tree, relation_type="Npr"):
    score_add = 0
    score_mult = 1
    mh_path = []

    for pair in l_pairs:
        # make pair into a tuple so it can be used as a dict key
        pair = tuple(pair)

        [mod, head] = pair

        if d_mh.has_key(pair):
            # count has already been computed and cached in dict d_mh
            count = d_mh2counts[pair]
        else:
            if relation_type == "Npr":
                # Given a mod and head in the NP order ("stem cells"), we compute the number of docs
                # spn is stemmed prev_Npr  "[ cells of "  as in "cells of human stem"
                # sp is stemmed NP "stem ]"  as last word in the phrase
                # we need to compute the count using elasticsearch query qc_mult
                count = qc_mult([head2spn(head), mod2sp(mod)], debug_p=False)
                d_mh[pair] = count
            elif relation_type == "fadj":
                # full adjacent (stemmed) phrase made up of the two terms
                count = qc_mult([["sp",  "[ " + mod + " | " + head + "  ]"]])
        mh_path.append([mod, head, count])    
        score_add += count
        # do laplace smoothing (+1 smoothing to avoid multiplying by 0)
        score_mult = score_mult * (count + 1)
    #print "bracketing: %s, %s, scores(add, mult): %i\t%i" % (tree, mh_path, score_add, score_mult)
    return([score_mult, score_add, tree, mh_path])

# path is a list of pairs of mod_index and head_index corresponding words
# l_words is list of words in a phrase
# d_mh is a dictionary with key = tuple[mod, head], value = count based on qc_mult result
# ie. based on count of spn, sp cooccurrence
def score_path(path, l_words, d_mh, ):
    score_add = 0
    score_mult = 1
    mh_path = []
    for pair in path:
        # make pair into a tuple so it can be used as a dict key
        pair = tuple(pair)

        [mod_index, head_index] = pair
        mod = l_words[mod_index]
        head = l_words[head_index]
        mh_path.append([mod, head])

        if d_mh.has_key(pair):
            # count has already been computed and cached in dict d_mh
            count = d_mh[pair]
        else:
            # we need to compute the count using elasticsearch query qc_mult
            count = qc_mult([head2spn(head), mod2sp(mod)], debug_p=False)
            d_mh[pair] = count
    
        score_add += count
        # do laplace smoothing (+1 smoothing to avoid multiplying by 0)
        score_mult = score_mult * (count + 1)
    print "path: %s, scores(add, mult): %i\t%i" % (mh_path, score_add, score_mult)
    
##################################

# **query templates

# To test that the index has content:
# curl -XGET localhost:9200/i_nps/_search?pretty=true&q={'matchAll':{''}}

# main function for querying NP's.
# contains a match_all query and optional set of bool filters
# does not compute rank.
# es_np.qmaf("sp", "term ]", [["year", 2000], ["doc_id", "pat1"]])
# es_np.qmaf("sp", "term ]", [["year", 2000], ["doc_id", "pat1"], ["domain", "cs"]] )
# es_np.qmaf("sp", "distortion ]", [["year", 1997], ["doc_id", "US5761382A"], ["domain", "computers"]] )
# es_np.qmaf("sp", "cell", index_name="i_np_bio", query_type="count")
# es_np.qmaf(field, value, l_must=[], doc_type="np", index_name="i_np_bio", query_type="search")
# es_np.qmaf("length", 3, l_must=[], doc_type="np", index_name="i_np_bio", query_type="search")
# es_np.qmaf("length", 2, index_name="test2", query_type="search")
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
        res = es.search(index=index_name, doc_type = doc_type, body=queryBody, size=100000)
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

# query applying match_phrase to multiple fields (and optional filters) 
# l_filter_must is a list of field/value term restrictions on unanalyzed fields, which are
# turned into { "term": { field : value }}
def qmamf(l_query_must=[], l_filter_must=[], l_fields=[], doc_type="np", index_name="i_nps_bio", query_type="search", debug_p=False):

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
        res = es.search(index=index_name, doc_type = doc_type, body=queryBody, size=100000)
    elif query_type == "count":
        res = es.count(index=index_name, doc_type = doc_type, body=queryBody)
    return(res)


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
# r = es_np.qp("phr", "system", fields=["phr"], size=20)
# r = es_np.qp("phr", "human skin fibroblast cell line", fields=["phr"])
# see http://stackoverflow.com/questions/21343549/can-i-specify-the-result-fields-in-elasticsearch-query
# returns the list of hits, restricted to the fields specified.
def qp(field, value, fields=["phr"], doc_type="np", index_name="i_nps_bio", pp=True, size=10000000):
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

# es_np.qs_mult([["spn", "[ skin" ], ["sp", "human ]" ]])
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

    res = es.search(index=index_name, doc_type = doc_type, body=queryBody, size=100000)
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
    res = es.search(index=index_name, doc_type = doc_type, body=queryBody, size=100000)
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
    res = es.search(index=index_name, doc_type = doc_type, body=queryBody, size=100000)
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

    res = es.search(index=index_name, doc_type = doc_type, body=queryBody, size=100000)
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

    res = es.search(index=index_name, doc_type = doc_type, body=queryBody, size=100000)
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
    
    res = es.search(index=index_name, doc_type = doc_type, body=queryBody, size=100000)
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
    
    res = es.search(index=index_name, doc_type = doc_type, body=queryBody, size=100000)
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

    res = es.search(index=index_name, doc_type = doc_type, body=queryBody, size=100000)
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
    res = es.search(index=index_name, doc_type = doc_type, body=queryBody, size=100000)
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


    res = es.search(index=index_name, doc_type = doc_type, body=queryBody, size=100000)
    return(res)



"""
ISSUES
Are unknown words treated correctly?

>>> es_np.bracket("zip stem cell research")     
bracketing: ['zip', [['stem', 'cell'], 'research']] 96 18 [['stem', 'cell', 11], ['cell', 'research', 7], ['zip', 'research', 0]]
bracketing: [['zip', ['stem', 'cell']], 'research'] 96 18 [['stem', 'cell', 11], ['zip', 'cell', 0], ['cell', 'research', 7]]
bracketing: [[['zip', 'stem'], 'cell'], 'research'] 96 18 [['zip', 'stem', 0], ['stem', 'cell', 11], ['cell', 'research', 7]]

We should incorporate prob of two word phrases where first word is beginning of phrase

Using the Npr allows us to catch cases where the NP is a short form of a relationship between between two nouns.  However,
this does not cover names or modifier relationship, as in
bracketing: [u'creatine', [u'kinase', u'activity']] 4295 862 [[u'kinase', u'activity', 858], [u'creatine', u'activity', 4]]
bracketing: [[u'creatine', u'kinase'], u'activity'] 859 858 [[u'creatine', u'kinase', 0], [u'kinase', u'activity', 858]]

or

bracketing: [u't', [u'cell', u'proliferation']] 20314 2907 [[u'cell', u'proliferation', 2901], [u't', u'proliferation', 6]]
bracketing: [[u't', u'cell'], u'proliferation'] 11608 2904 [[u't', u'cell', 3], [u'cell', u'proliferation', 2901]]

Thus, we need to integrate evidence from different types of np formation.

relational NP prep NP
verbal V NP
dispersion of head term in complete NP bigrams
prob mod given dom
prob dom given mod

want to score each mod head pair in dominance tree using multiple indicators

using chi square (from Nakov paper)

A #(w1,w2) cooccurences in mod-dom relationship
B #(w1, !w2) occurrences of w1 as mod without w2 as head
C #(!w1, w2) occurrences of w2 as head without w1 as mod
D N - A - B - C
N A+B+C+D total number of bigrams (head-mod relations) = Npr + ((length of all phrases) - # phrases)
each phrase can have n - 1 dom/mod relations in it.

estimate based on (1) % of phrases that have an Npr relation
(2) the average length of a phrase

length of all phrases = average length * number of phrases
#Npr = number of phrases * % phrases containing Npr 

Types of compounds
relational (verbal)
subtype (a isa b)
adjectival
proper-name
name subtype (ab isa b)

Another possible indicator: # times terms appear in same sentence or nearby sentence.  This would help with contextually
based NC's such as malaria mosquitos

BUGS:

Some phrases must have extra ws in them, resulting in such phrases in our index:
{u'phr': [u'| | | | | | | | | |']}
{u'phr': [u'| | | | | | | | | |']}
{u'phr': [u'| | | | | | | | | |']}
{u'phr': [u'| | | | | | | | | |']}
{u'phr': [u'| | | | | | | | | |']}
{u'phr': [u'ctgcctgtcccaatgctc-agcc | | | | | | | | | | | | | | | | | | | | ctgcctgtccc']}

idea: local compound resolution.  Work from beginning of doc.  Track binary compounds and Npr relations.  For each 
compound with length > 2, can it be resolved using previously seen compounds?  If not, put it on TBD list.  
At end of doc, retry all TBD compounds.  Those that cannot be solved locally go on NLC list (nonlocal compound list), to be
solved using global means.  Perhaps they can be partially solved locally.

output: number of compounds solvable by prior context.  
number solvable by local context
number solvable by global context
compare to solving them all by global context.

"""
