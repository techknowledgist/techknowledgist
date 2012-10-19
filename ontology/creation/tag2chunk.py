# tag2chunk.py

# TODO: remove __ from front of chunks in phr_feats

# for chunks doc (identify all chunks in a doc and output two files, 
# one with all chunks indexed by id with all features for that phrase occurrence (phr_feats)
# one with only chunk and <id><tab><bracketed sentence>, to be used for annotation)

import os
import codecs
import sentence

# returns True if lists share at least one term
def share_term_p(l1, l2):
    for term in l1:
        if term in l2:
            return True
    return False

# symbol without blanks, with name and value separated by "__"
# name should be a string without blanks
# value should be a string and may contain blanks
def mallet_feature(name, value):
    value_separator = "="
    if value == "":
        return("")
    else:
        symbol = value.strip(" ").replace(" ", "_")
        feature = name + value_separator + symbol
        #print "created feature: %s" % feature
        return(feature)
    

class Doc:

    def __init__(self, input,  output_phr_occ, output_phr_feats, year, lang):
        self.input = input
        # PGA made year a parameter so not dependent on path structure 10/9/12
        #self.year = input.split(os.sep)[-2]
        self.year = year
        self.output_phr_occ = output_phr_occ
        self.output_phr_feats = output_phr_feats
        self.chunk_schema = sentence.d_chunkSchema.get(lang)
        self.lang = lang
        # field_name to list of sent instances
        # field name is header string without FH_ or : affixes
        self.d_field = {}
        
        # sent id to sent instance
        self.next_sent_id = 0
        self.d_sent = {}
        # chunk id to chunk instance
        self.next_chunk_id = 0
        self.d_chunk = {}

        # lc noun tokens appearing in title
        self.l_lc_title_noun = []

        # create the chunks
        self.process_doc()
        

    # process the doc, creating all potential technology chunks
    def process_doc(self):
        debug_p = False
        s_input = codecs.open(self.input, encoding='utf-8')
        s_output_phr_occ = open(self.output_phr_occ, "w")
        s_output_phr_feats = open(self.output_phr_feats, "w")
        #s_output_chunk = open(self.output_chunk, "w")

        section = "FH_NONE"   # default section if document has no section header lines
        self.d_field[section] = []

        sent_no_in_section = 0
        for line in s_input:
            line = line.strip("\n")

            if line[0:3] == "FH_":
                # we are at a section header
                # note we have to strip off both final : and ws, since in some cases
                # eg. Chinese segmentation, the colon will be separated from the header term 
                # by a blank.
                section = line.split("_")[1].rstrip(": ")
                self.d_field[section] = []
                # reset the line count
                sent_no_in_section = 0
            else:
                if debug_p:
                    print "[chunk]line: %s" % line
                # process the sentences in the section
                # The line is actually a tag_string
                tag_string = line

                if debug_p:
                    print "[chunk]tag_string: %s" % tag_string
                #print "ncontext:"
                #s1.ncontext()
                if section == "TITLE" or section == "ABSTRACT":
                    #print "[process_doc] found title or abstract"
                    self.l_lc_title_noun.extend(lc_nouns(tag_string))

                # call the appropriate Sentence subclass based on the language (get_sentence_for_lang)
                sent_args = [self.next_sent_id, section, sent_no_in_section, tag_string, self.chunk_schema]
                sent = sentence.get_sentence_for_lang(self.lang, sent_args)
                ###print "[process_doc]sent: %s" % sent

                # get context info
                i = 0
                for chunk in sent.chunk_iter():
                    if chunk.label == "tech":
                        # index of chunk start in sentence => ci
                        ci = chunk.chunk_start

                        # generate features

                        m_chunk = mallet_feature("", chunk.phrase.lower())
                        # remove the __ separator at the beginning of the chunk, since we don't
                        # really need it
                        m_chunk = m_chunk[1:]
                        hsent = sent.highlight_chunk(i)

                        """
                        field in chunk (features) output line
                        6 prev_n
                        7 next_n
                        8 prev_V
                        9 prev_N
                        10 initial_J
                        11 initial_V
                        12 following_prep
                        13 of_head
                        14 last_word
                        15 tag_sig
                        16 hsent
                        """
                        # call all feature_methods for the current sentence and create a list of their 
                        # results, which should be expressed as mallet features (name=value) or None
                        mallet_feature_list = []
                        for method in sent.feature_methods:
                            result = method(sent, ci) # unbound methods, so must supply instance
                            if result != None:
                                mallet_feature_list.append(result)

                        uid = os.path.basename(self.input) + "_" + str(self.next_chunk_id)

                        year = self.year

                        # meta data to go at beginning of phr_feats output lines
                        metadata_list = [uid, year, chunk.phrase.lower()]

                        # remove empty features from the list                                                                                         
                        if debug_p:
                            print "index: %i, start: %i, end: %i, sentence: %s" % \
                                (i, chunk.chunk_start, chunk.chunk_end, sent.sentence)

                        # FILTERING technology terms to output
                        # Here we only output terms that are in the title or share a term with a title term
                        # Note that our "title terms" can actually come from title or abstract.   Many German
                        # patent titles are only one word long!
                        if section == "TITLE" or share_term_p(self.l_lc_title_noun, chunk.lc_tokens):
                            # write out the phrase occurrence data (phr_occ)
                            # For each phrase occurrence, include uid, year, phrase and full sentence (with highlighted chunk)
                            #print "matched term for %s and %s" %  (self.l_lc_title_noun, chunk.lc_tokens)
                            unlabeled_out = "\t".join([uid, self.year, chunk.phrase.lower(), hsent + '\n'])

                            unlabeled_out = unlabeled_out.encode('utf-8')
                            s_output_phr_occ.write(unlabeled_out)
                            
                            # create a tab separated string of features to be written out to phr_feats
                            # The full line includes metadata followed by features
                            metadata_list.extend(mallet_feature_list)
                            full_list = metadata_list
                            mallet_feature_string = "\t".join(full_list) + '\n'
                            mallet_feature_string = mallet_feature_string.encode('utf-8')

                            s_output_phr_feats.write(mallet_feature_string)
                            ###print "mallet_feature string: %s" % mallet_feature_string
                            
                        if debug_p:
                            print ""

                        chunk.sid = self.next_sent_id

                        self.d_chunk[self.next_chunk_id] = chunk
                        sent.chunks.append(chunk)
                        self.next_chunk_id += 1

                    i = chunk.chunk_end
                    
                # keep track of the location of this sentence within the section
                sent_no_in_section += 1
                #print "[process_doc]section: |%s|" % section
                self.d_field[section].append(sent)
                self.d_sent[self.next_sent_id] = sent
                self.next_sent_id += 1
                
        s_input.close()
        s_output_phr_occ.close()
        s_output_phr_feats.close()

def tag2chunk_dir(tag_dir, phr_occ_dir, phr_feats_dir, year, lang):
    #output_chunk = "/home/j/anick/fuse/data/patents/en_test/chunk/US20110052365A1.xml"
    for file in os.listdir(tag_dir):
        input = tag_dir + "/" + file
        output_phr_occ = phr_occ_dir + "/" + file
        output_phr_feats = phr_feats_dir + "/" + file

        doc = Doc(input, output_phr_occ, output_phr_feats, year, lang)

# tag2chunk.test_t2c()
def test_t2c():
    input = "/home/j/anick/fuse/data/patents/en_test/tag/US20110052365A1.xml"
    output_phr_occ = "/home/j/anick/fuse/data/patents/en_test/phr_occ/US20110052365A1.new2.xml"
    output_phr_feats = "/home/j/anick/fuse/data/patents/en_test/phr_feats/US20110052365A1.new2.xml"
    #cs = sentence.chunk_schema("en")
    year = "1980"
    lang = "en"
    doc = Doc(input, output_phr_occ, output_phr_feats, year, lang)
    return(doc)


# tag2chunk.test_t2c()
def test_t2c_de():
    
    input = "/home/j/anick/fuse/data/patents/de/tag/1982/DE3102424A1.xml"
    output_phr_occ = "/home/j/anick/fuse/data/patents/de_test/DE3102424A1.phr_occ"
    output_phr_feats = "/home/j/anick/fuse/data/patents/de_test/DE3102424A1.phr_feats"
    cs = sentence.chunk_schema("de")

    year = "1980"
    lang = "de"
    doc = Doc(input, output_phr_occ, output_phr_feats, year, lang)
    return(doc)

# tag2chunk.test_t2c_de_tag_sig()
def test_t2c_de_tag_sig():
    
    input = "/home/j/anick/fuse/data/patents/de_test/tag_sig_test.xml"
    output_phr_occ = "/home/j/anick/fuse/data/patents/de_test/tag_sig_test.phr_occ"
    output_phr_feats = "/home/j/anick/fuse/data/patents/de_test/tag_sig_test.phr_feats"
    cs = sentence.chunk_schema("de")

    year = "1982"
    lang = "de"
    doc = Doc(input, output_phr_occ, output_phr_feats, year, lang)
    return(doc)


# tag2chunk.test_t2c_cn()
def test_t2c_cn():
    input = "/home/j/anick/fuse/data/patents/tmp/cn/CN1394959A-tf.tag"
    output_phr_occ = "/home/j/anick/fuse/data/patents/cn_test/CN1394959A-tf.new.phr_occ"
    output_phr_feats = "/home/j/anick/fuse/data/patents/cn_test/CN1394959A-tf.new.phr_feats"
    year = "1980"
    lang = "cn"
    doc = Doc(input, output_phr_occ, output_phr_feats, year, lang)
    return(doc)



# returns (lowercased) nouns in a tag_string
def lc_nouns(tag_string):

    l_lc_nouns = []
    for tagged_token in tag_string.split(" "):
        (tok, tag) = tagged_token.rsplit("_", 1)
        if tag[0:1] == "N":
            l_lc_nouns.append(tok.lower())
    return(l_lc_nouns)


# language is en, de, cn
# lang_path (above year_dir)
# e.g. tag2chunk.patent_tag2chunk_dir("/home/j/anick/fuse/data/patents", "de")
def patent_tag2chunk_dir(patent_path, language):
    lang_path = patent_path + "/" + language
    phr_occ_path = lang_path + "/phr_occ"
    phr_feats_path = lang_path + "/phr_feats"
    tag_path = lang_path + "/tag"
    c_schema = sentence.chunk_schema(language)
    for year in os.listdir(tag_path):
        phr_occ_year_dir = phr_occ_path + "/" + year
        phr_feats_year_dir = phr_feats_path + "/" + year
        tag_year_dir = tag_path + "/" + year
        #print "[patent_tag2chunk_dir]calling tag2chunk for dir: %s" % tag_year_dir
        print "[patent_tag2chunk_dir]calling tag2chunk, output dirs: %s, %s" % (phr_feats_year_dir, phr_occ_year_dir)
        tag2chunk_dir(tag_year_dir, phr_occ_year_dir, phr_feats_year_dir, year, language)
    print "[patent_tag2chunk_dir]finished writing chunked data to %s and %s" % (phr_occ_path, phr_feats_path)

### debugging _no output produced PGA 10/8
def pipeline_tag2chunk_dir(root, language):
    
    phr_occ_path = root + "/phr_occ"
    phr_feats_path = root + "/phr_feats"
    tag_path = root + "/tag"
    #c_schema = sentence.chunk_schema(language)
    # The only way to determine the year for a file is to look in file_list.txt
    d_file2year = {}
    file_list_file = os.path.join(root, "file_list.txt")
    s_list = open(file_list_file)
    year = ""
    file_path = ""
    for line in s_list:
        (id, year, path) = line.split(" ")
        # create the file name from id + .xml
        file_name = id + ".xml"
        tag_file = os.path.join(root, "tag", file_name)

        output_phr_occ = os.path.join(root, "phr_occ", file_name)
        output_phr_feats = os.path.join(root, "phr_feats", file_name)

        print "[pipeline_tag2chunk_dir]about to process doc: %s, phr_occ: %s, phr_feats: %s, year: %s" % (tag_file, output_phr_occ, output_phr_feats, year)
        doc = Doc(tag_file, output_phr_occ, output_phr_feats, year, language)


    s_list.close()

    print "[pipeline_tag2chunk_dir]finished writing chunked data to %s and %s" % (phr_occ_path, phr_feats_path)


# top level call to tag txt data dir in a language
# tag2chunk.chunk_lang("en")
# tag2chunk.chunk_lang("de")
# tag2chunk.chunk_lang("cn")
def chunk_lang(lang):
    patent_path = "/home/j/anick/fuse/data/patents"
    patent_tag2chunk_dir("/home/j/anick/fuse/data/patents", lang)
