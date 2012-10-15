# tag2chunk.py

# TODO: remove __ from front of chunks in phr_feats

# for chunks doc (identify all chunks in a doc and output two files, 
# one with all chunks indexed by id with all features for that phrase occurrence (phr_feats)
# one with only chunk and <id><tab><bracketed sentence>, to be used for annotation)

import os
import codecs
from xml.sax.saxutils import escape

# returns True if lists share at least one term
def share_term_p(l1, l2):
    for term in l1:
        if term in l2:
            return True
    return False

# combines a doc section (header) with either 0 (if chunk appears in first
# sentence of section) or 1 is it appears later.
def make_section_loc(section, sent_no_in_section):
    loc = ""
    if sent_no_in_section == 0:
        loc = "sent1"
    else:
        loc = "later"
    section_loc = section + "_" + loc
    return(section_loc)

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

    def __init__(self, input,  output_phr_occ, output_phr_feats, chunk_schema, year):
        self.input = input
        # PGA made year a parameter so not dependent on path structure 10/9/12
        #self.year = input.split(os.sep)[-2]
        self.year = year
        self.output_phr_occ = output_phr_occ
        self.output_phr_feats = output_phr_feats
        self.chunk_schema = chunk_schema
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
                sent = Sent(self.next_sent_id, section, sent_no_in_section, tag_string, self.chunk_schema)

                # get context info
                i = 0
                for chunk in sent.chunk_iter():
                    if chunk.label == "tech":
                        # index of chunk start in sentence => ci
                        ci = chunk.chunk_start

                        # generate features

                        section_loc = make_section_loc(section, sent_no_in_section)
                        prev_n3 = sent.prev_n(ci, 3)
                        next_n3 = sent.next_n(ci, 3)
                        prev_V = sent.prev_V(ci)
                        prev_N = sent.prev_N(ci)
                        initial_J = sent.initial_J(ci)
                        initial_V = sent.initial_V(ci)
                        following_prep = sent.following_prep(ci)
                        of_head = sent.of_head(ci)
                        last_word = sent.last_word(ci)
                        tag_sig = sent.tag_sig(ci)
                        prev_n2 = sent.prev_n(ci, 2)
                        next_n2 = sent.next_n(ci, 2)
                        next_2tags = sent.next_n_tags(ci, 2)
                        lead_J = sent.chunk_lead_J(ci)
                        lead_VBG = sent.chunk_lead_VBG(ci)


                        m_chunk = mallet_feature("", chunk.phrase.lower())
                        # remove the __ separator at the beginning of the chunk, since we don't
                        # really need it
                        m_chunk = m_chunk[1:]
                        m_section = mallet_feature("section", section)
                        m_section_loc = mallet_feature("section_loc", section_loc)
                        m_prev_n3 = mallet_feature("prev_n3", prev_n3 )
                        m_next_n3 = mallet_feature("next_n3", next_n3 )
                        m_prev_V = mallet_feature("prev_V", prev_V)
                        m_prev_N = mallet_feature("prev_N", prev_N)
                        m_initial_J = mallet_feature("initial_J", initial_J)
                        m_initial_V = mallet_feature("initial_V", initial_V)
                        m_following_prep = mallet_feature("following_prep", following_prep)
                        m_of_head = mallet_feature("of_head", of_head)
                        m_last_word = mallet_feature("last_word", last_word)
                        m_tag_sig = mallet_feature("tag_sig", tag_sig)
                        m_prev_n2 = mallet_feature("prev_n2", prev_n2)
                        m_next_n2 = mallet_feature("next_n2", next_n2)
                        m_next_2tags = mallet_feature("next_2tags", next_2tags)
                        m_lead_J = mallet_feature("lead_J", lead_J)
                        m_lead_VBG = mallet_feature("lead_VBG", lead_VBG)

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
                        
                        #feature_list = [self.input, section, str(sent_no_in_section), str(self.next_chunk_id), chunk.phrase.lower(), prev_n3, next_n3, prev_V, prev_N, initial_J, initial_V, following_prep, of_head, last_word, tag_sig, prev_n2, next_n2, next_2tags, hsent, "\n"]

                        chunk_list = [chunk.phrase.lower(), hsent, "\n"]
                        feature_list = [chunk.phrase.lower()[2:], section, section_loc,  prev_n3, next_n3, prev_V, prev_N, initial_J, initial_V, following_prep, of_head, last_word, tag_sig, prev_n2, next_n2, next_2tags, hsent, "\n"]
                        pre_mallet_feature_list = [m_chunk, m_section, m_section_loc, m_prev_n3, m_next_n3, m_prev_V, m_prev_N, m_initial_J, m_initial_V, m_following_prep, m_of_head, m_last_word, m_tag_sig, m_prev_n2, m_next_n2, m_next_2tags, m_lead_J, m_lead_VBG, "\n"]

                        uid = os.path.basename(self.input) + "_" + str(self.next_chunk_id)

                        # remove empty features from the list
                        mallet_feature_list = [uid]

                        # PGA 10/7                                                                                                                    
                        year = self.year

                        # meta data at beginning of mallet feature list
                        mallet_feature_list = [uid, year, chunk.phrase.lower()]

                        # remove empty features from the list                                                                                         
                        for feature in pre_mallet_feature_list:
                            if feature != "":
                                mallet_feature_list.append(feature)

                        # PGA removed 10/7
                        """
                        chunk_string = "\t".join(chunk_list)
                        chunk_string = chunk_string.encode('utf-8')

                        feature_string = "\t".join(feature_list)
                        feature_string = feature_string.encode('utf-8')
                        """

                        if debug_p:
                            print "index: %i, start: %i, end: %i, sentence: %s" % \
                                (i, chunk.chunk_start, chunk.chunk_end, sent.sentence)

                        if section == "TITLE" or share_term_p(self.l_lc_title_noun, chunk.lc_tokens):
                            #print "matched term for %s and %s" %  (self.l_lc_title_noun, chunk.lc_tokens)
                            unlabeled_out = "\t".join([uid, self.year, chunk.phrase.lower(), hsent + '\n'])

                            unlabeled_out = unlabeled_out.encode('utf-8')
                            s_output_phr_occ.write(unlabeled_out)
                            
                            mallet_feature_string = "\t".join(mallet_feature_list)
                            mallet_feature_string = mallet_feature_string.encode('utf-8')

                            s_output_phr_feats.write(mallet_feature_string)
                            #print "mallet_feature string: %s" % mallet_feature_string
                            
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

        
class Sent:

    # given a tag_string, generate all chunks in the sentence in a chart
    # data structure
    # e.g. 'John_NNP went_VBD today_NN ._.'
    def __init__(self, sid, field, num, tag_string, chunk_schema):
        self.debug_p = False
        #self.debug_p = True
        # make sure there are no ws on edges since we will split on ws later
        self.tag_string = tag_string.strip(" ")
        self.len = 0
        self.last = 0
        self.sentence = ""
        self.toks = []
        self.tags = []
        # list of chunk instances within sent
        self.chunks = []
        # sid is number of sentence within entire document
        self.sid = sid
        # name of field (section) in which the sentence occurs
        self.field = field
        # number of sentence within the field
        self.num = num

        # chart is a sequence of chunk instances, one for each token
        self.chart = []
        self.init_chart(tag_string)
        self.chunk_chart_tech(chunk_schema)

    # create initial chart using raw token list
    def init_chart(self, tag_string):
        if self.debug_p:
            print "[init_chart]tag_string: %s" % tag_string
        self.tags = tag_string.split(" ")
        self.len = len(self.tags)
        self.last = self.len - 1
        l_tok = []
        index = 0
        next = 1
        for tag in self.tags:
            # use rsplit with maxsplit = 1 so that we don't further split tokens like CRF07_BC
            (tok, tag) = tag.rsplit("_", 1)
            chunk = Chunk(index, next, tok, tag)
            self.chart.append(chunk)
            l_tok.append(tok)
            index += 1
            next += 1
        # create the sentence
        self.sentence = " ".join(l_tok)
        self.toks = l_tok

    # fill out phrasal chunks in the chart
    # This uses the patterns in the chunk_schema to combine tokens into a chunk
    # The chunk must end in certain toks, so we keep track of the last legal end token
    # and if it differs from the actual end token (such as a conjunction or adjective),
    # we create the chunk up to the last legal end token.
    def chunk_chart_tech(self, chunk_schema):

        # True when we are inside of a chunk
        # used to know if we should continue chunking based on
        # start chunk constraints or continue chunk constraints.
        inChunk_p = False

        #print "[Sent chunk]%s" % self.chart
        # last tag
        last_tag = " "

        # start index of current chunk
        cstart = 0

        # index of the last legal end token for a chunk
        last_legal_end_index = -1
        last_legal_phrase = ""
        # list of tags in a chunk
        last_legal_chunk_tags = []

        if self.debug_p:
            print "[chunk_chart]self.len: %i" % self.len
        for i in range(self.len):
            if self.debug_p:
                print "[chunk_chart]i: %i" % i

            chunk = self.chart[i]
            # check if chunk has same tag group as previous token
            if self.chunkable_p(chunk, inChunk_p, chunk_schema):
                # If this token starts a chunk, advance cstart to this token.
                # Otherwise cstart should already be the index of the first token in this chunk.
                if not inChunk_p:
                    cstart = i
                # extend the start chunk by concatenating the current token to the 
                # chunk token stored at the start index of the chunk.
                self.chart[cstart].chunk_end = i + 1

                if self.debug_p:
                    print "chunk phrase: |%s|, start: %i" % (self.chart[cstart].phrase, cstart)
                if not inChunk_p:
                    # set the label for the first element in the chunk to "tech"
                    self.chart[cstart].label = "tech"
                    # start the phrase using the current token
                    #self.chart[cstart].phrase = self.chart[cstart].phrase + " " + chunk.tok
                    self.chart[cstart].phrase = chunk.tok
                else:
                    # continue the phrase by concatenation
                    self.chart[cstart].phrase = self.chart[cstart].phrase + " " + chunk.tok

                self.chart[cstart].chunk_tags.append(chunk.tag)
                self.chart[cstart].tokens.append(chunk.tok)
                self.chart[cstart].lc_tokens.append(chunk.tok.lower())
                inChunk_p = True
                # check if this token could be a legal end
                if self.legal_end_p(chunk, chunk_schema):
                    last_legal_end_index = i
                    # update the last legal phrase
                    last_legal_phrase = self.chart[cstart].phrase
                    last_legal_chunk_tags = self.chart[cstart].chunk_tags
            else:
                # terminate chunk
                # make sure the phrase and index correspond to the last legal end
                # We'll throw away any tokens up to the last legal ending of a chunk.
                if last_legal_end_index > -1:
                    self.chart[cstart].phrase = last_legal_phrase
                    self.chart[cstart].chunk_tags = last_legal_chunk_tags
                    self.chart[cstart].chunk_end = last_legal_end_index + 1
                else:
                    # reset the start chunk to remove all (now invalidated) phrasal info
                    self.chart[cstart].label = ""
                    self.chart[cstart].chunk_end = self.chart[cstart].tok_end + 1
                    self.chart[cstart].phrase = self.chart[cstart].tok
                    self.chart[cstart].chunk_tags = []

                # last_legal_chunk_tags tracks the last set of terms that 
                # includes a legitimate end term.  We use this if we reach the end of a chunk
                # at an illegal termination token and need to back up.
                last_legal_chunk_tags = []

                last_legal_end_index = -1
                cstart = i
                inChunk_p = False

    def legal_end_p(self, chunk, chunk_schema):
        # return True if this token can legally end a chunk
        try:
            if self.debug_p:
                print "[legal_end_p]in chunk, tok: %s" % chunk.tok
            pat = chunk_schema.d_end[chunk.tag]
            
            # check constraints
            if self.debug_p:
                print "[legal_end_p]pat: %s, tag: %s" % (pat, chunk.tag)
            test_val = False
            if pat != []:
                if pat[0] == "-" and chunk.tok.lower() not in pat[1:]:
                    test_val == True
                else:
                    test_val == False
                if self.debug_p:
                    print "[legal_end_p](pat[0] == - and chunk.tok.lower() not in pat[1:]): %r" % (test_val)
            if (pat == []) or (pat[0] == "-" and chunk.tok.lower() not in pat[1:]) or (pat[0] == "+" and chunk.tok.lower() in pat[1:]):
                if self.debug_p:
                    print "[legal_end_p] matched!"
                return True
            else:
                return False
        except KeyError:
            return False
        
    # returns True if the current token/tag is part of a chunk according to
    # the patterns stored in chunk_schema and the current state (either in a
    # chunk or not).
    def chunkable_p(self, chunk, inChunk_p, chunk_schema):
        # match the chunk pattern depending on whether starting or
        # continuing a chunk
        # If the tag is not in our pattern, then return false
        self.debug_p = False
        try:
            if inChunk_p:
                if self.debug_p:
                    print "[chunkable]in chunk, tok: %s" % chunk.tok
                pat = chunk_schema.d_cont[chunk.tag]
            else:
                if self.debug_p:
                    print "[chunkable]NOT yet in chunk, tok: %s" % chunk.tok
                pat = chunk_schema.d_start[chunk.tag]

            # check constraints
            if self.debug_p:
                print "[chunkable_p]pat: %s, inChunk_p: %s, tag: %s" % (pat, inChunk_p, chunk.tag)
            test_val = False
            if pat != []:
                if pat[0] == "-" and chunk.tok.lower() not in pat[1:]:
                    test_val == True
                else:
                    test_val == False
                if self.debug_p:
                    print "[chunkable_p](pat[0] == - and chunk.tok.lower() not in pat[1:]): %r" % (test_val)
            if (pat == []) or (pat[0] == "-" and chunk.tok.lower() not in pat[1:]) or (pat[0] == "+" and chunk.tok.lower() in pat[1:]):
                if self.debug_p:
                    print "[chunkable_p] matched!"
                return True
            else:
                return False
        except KeyError:
            return False

    def __display__(self):
        print "[Sent] %s" % self.tag_string
        for chunk in self.chart:
            chunk.__display__()

    # return sentence with np tag around the chunk starting at index
    def highlight_chunk(self, index):
        l_tok = self.toks
        last_tok = self.chart[index].chunk_end - 1
        l_highlight = []
        i = 0
        for tok in l_tok:
            if i == index:
                l_highlight.append("<np>")
            l_highlight.append(escape(tok))
            #l_highlight.append(tok)
            if i == last_tok:
                l_highlight.append("</np>")
            i += 1

        hsent = " ".join(l_highlight)
        return(hsent)
    
    def chunk_iter(self):
        chunk = self.chart[0]
        while True:
            #chunk.__display__()
            yield(chunk)
            if chunk.chunk_end < self.len:
                #print "[chunk_iter]chunk_end: %i" % chunk.chunk_end
                chunk = self.chart[chunk.chunk_end]
            else:
                #print "[chunk_iter before break]chunk_end: %i" % chunk.chunk_end
                break

    # returns the string of up to count tokens prior to index
    # if no tokens exist, it includes "^"
    def prev_n(self, index, count):
        prev_n_string = ""
        start = index - count

        i = start
        while i < index:
            if i < 0:
                prev_n_string = prev_n_string + " ^"
            else:
                prev_n_string = prev_n_string + " " + self.chart[i].tok
            i += 1
        return(prev_n_string.lower())

    def next_n(self, index, count):
        ##print "[next_n]tag_string: %s" % self.tag_string
        next_n_string = ""
        end = self.chart[index].chunk_end + count
        sent_end = self.len - 1
        

        ##print "\n\n[next_n]chunk_end: %i, end: %i, sent_end: %i" % (self.chart[index].chunk_end, end, sent_end)
        ##print "[next_n]self.len: %i, tag_string: |%s|" % (self.len, self.tag_string)
        ##print "[next_n]current_chunk: %s" % self.chart[index].phrase

        # start just after chunk ends
        i = self.chart[index].chunk_end
        while i < end:
            if i > sent_end:
                next_n_string = next_n_string + " ^"
            else:
                next_n_string = next_n_string + " " + self.chart[i].tok
            i += 1
        return(next_n_string.lower())

    def next_n_tags(self, index, count):
        next_n_string = ""
        end = (self.chart[index].chunk_end + count) - 1
        sent_end = self.len - 1
        if sent_end < end:
            end = sent_end

        # start just after chunk ends
        i = self.chart[index].chunk_end
        while i <= end:
            next_n_string = next_n_string + " " + self.chart[i].tag
            i += 1
        return(next_n_string)


    # previous verb
    # return closest verb to left of NP
    # as well as prep or particle if there is one after verb
    def prev_V(self, index):
        verb = ""
        prep = ""
        verb_prep = ""
        i = index -1
        while i > 0:
            # terminate if verb is found
            if self.chart[i].tag[0] == "V":
                verb = self.chart[i].tok
                break
            # terminate if a noun is reached before a verb
            if self.chart[i].tag[0] == "N":
                break
            # keep a prep if reached before verb
            if self.chart[i].tag[0] in ["RP", "IN"]:
                prep = self.chart[i].tok
            else:
                # keep looking 
                i = i - 1
        if verb != "":
            verb_prep = verb + " " + prep
        return(verb_prep.lower())

    # first noun to the left of chunk, within 3 words
    def prev_N(self, index):
        noun = ""
        i = index - 1
        distance_limit = 3
        while i > 0 and distance_limit > 0:
            # terminate if verb is found
            if self.chart[i].tag[0] == "N":
                noun = self.chart[i].tok
                break
            else:
                # keep looking 
                i = i - 1

            distance_limit = distance_limit - 1
        return(noun.lower())

    # find index of the first prep in the chunk
    # Used to identify location of a PP
    # returns -1 if no prep
    def first_prep_idx(self, index):
        i = index
        chunk_end_loc = self.chart[index].chunk_end
        while i < chunk_end_loc:
            if self.chart[i].tag == "IN":
                return(i)
            i += 1
        return(-1)

    # initial adj in chunk, if there is one
    def chunk_lead_J(self, index):
        if self.chart[index].tag[0] == "J":
            return(self.chart[index].tok)
        else:
            return("")

    # initial V-ing verb in chunk, if there is one
    def chunk_lead_VBG(self, index):
        if self.chart[index].tag[0] == "VBG":
            return(self.chart[index].tok)
        else:
            return("")


    # head of prep in chunk, if there is one
    def of_head(self, index):
        i = index
        head = ""
        prep_idx = self.first_prep_idx(index)
        if prep_idx == -1:
            #print "[of_head]index: %i, tok: %s, lc_tokens: %s" % (index, self.chart[index].tok, self.chart[index].lc_tokens)
            #head = self.chart[index].lc_tokens[-1]
            return("")
        else:
            head_loc = prep_idx - 1
            head = self.chart[head_loc].tok
        return(head.lower())

    # previous adj (JJ, JJR, JJS)
    # Adj must be immediately bfore index term
    def prev_J(self, index):
        i = index - 1
        if self.chart[i].tag[0] == "J":
            return(self.chart[i].tok.lower())
        else:
            return("")
    # first adjective in the chunk
    def initial_J(self, index):
        i = index
        if self.chart[i].tag[0] == "J":
            return(self.chart[i].tok.lower())
        else:
            return("")

    def initial_V(self, index):
        i = index
        if self.chart[i].tag[0] == "V":
            return(self.chart[i].tok.lower())
        else:
            return("")

    # If a prep occurs directly after the chunk, return the token
    def following_prep(self, index):
        i = index
        following_index = self.chart[i].chunk_end
        if following_index <= self.last:
            if self.chart[following_index].tag == "IN":
                return(self.chart[following_index].tok.lower())
        return("")
            
    def last_word(self, index):
            last_index = self.chart[index].chunk_end - 1
            return(self.chart[last_index].tok.lower())

    # tag signature (sequence of tags as a string)
    def tag_sig(self, index):
        tag_string = "_".join(self.chart[index].chunk_tags)
        return(tag_string)

        
class Chunk:
    
    def __init__(self, tok_start, tok_end, tok, tag ):
        self.sid = -1  # sentence id (set in process_doc)
        self.tok_start = tok_start
        self.tok_end = tok_end
        self.tok = tok
        self.tag = tag
        # label is changed if a chunk pattern is matched
        self.label = tag
        # if not a multi-token chunk, chunk_start/end should be same as
        # tok_start/end
        self.chunk_start = tok_start
        self.chunk_end = tok_end
        self.head = ""
        self.of_head = ""
        self.phrase = ""
        # list of strings 
        self.tokens = []
        self.lc_tokens = []
        self.premods = []
        self.postmod = None  # connector + NOMP
        self.precontext = []
        self.postcontext = []
        # list of tags in a phrasal chunk
        self.chunk_tags = []
        # for head idx, -1 means no head found
        self.head_idx = -1
        self.prep_head_idx = -1
        self.chunk_lead_J = ""
        self.chunk_lead_VBG = ""

    # return the token loc in sentence for head of the chunk
    def head_idx(self):
        idx = self.tok_start
        head_idx = idx
        l_tags = self.chunk_tags
        for tag in l_tags:

            # check for termination conditions
            if tag in ["IN", "DT", "CC"]:
                break
            else:
                head_idx = idx    
            idx += 1

        # for debugging, print the idx within the phrase, rather than within the sentence
        rel_idx = head_idx - self.tok_start
        #print "[head_idex]rel_idx: %i" % rel_idx
        return(idx)

    # return the index of the head of a prep phrase in the chunk, if there is one.  If not
    # return -1.
    def prep_head_idx(self):
        idx = self.tok_start
        head_idx = -1
        l_tags = self.chunk_tags
        prep_found_p = False
        nv_found_p = False
        for tag in l_tags:

            if prep_found_p == True:
                # check for termination conditions
                if tag in ["IN"]:
                    break
                else:
                    if tag[0] == "N" or tag[0] == "V":
                        head_idx = idx    
                        nv_found_p = True
            # is the tag a prep?
            if tag == "IN":
                prep_found_p = True
            idx += 1

        # for debugging, print the idx within the phrase, rather than within the sentence
        rel_idx = head_idx - self.tok_start
        #print "[prep_head_idx]rel_idx: %i" % rel_idx
        return(idx)
            

    def __display__(self):
        print "Chunk type: %s, phrase: %s, %i, %i" % (self.tag, self.phrase, self.chunk_start, self.chunk_end)

# instance of a chunk definition in the form of two dictionaries:
# conditions for matching the start of a chunk (tags + token constraints)
# conditions for continuing a chunk (tags + token constraints)
class chunkSchema:
    
    def __init__(self, start_pat, cont_pat, end_pat):
        self.d_start = {}
        self.d_cont = {}
        self.d_end = {}
        for pat in start_pat:
            key = pat[0]
            value = pat[1]
            self.d_start[key] = value
        for pat in cont_pat:
            key = pat[0]
            value = pat[1]
            self.d_cont[key] = value
        for pat in end_pat:
            key = pat[0]
            value = pat[1]
            self.d_end[key] = value


# constraints are indicated by 
# "-" none of the following strings
# "+" only the following strings
# [] no constraints
# end_pat are the legal POS that can end a chunk
#def chunk_schema_en():
def chunk_schema(lang):
    start_pat = []
    cont_pat = []
    end_pat = []
    
    if lang == "en":
        both_pat =  [ ["NN", []], ["NNP", []], ["NNS", []], ["NNPS", []], ["POS", []],  ["JJ", ["-", "further", "such", "therebetween", "same", "following", "respective", "first", "second", "third", "fourth", "respective", "preceding", "predetermined", "next", "more"] ], ["JJR", ["-", "more"] ], ["JJS", [] ], ["FW", ["-", "e.g.", "i.e"] ], ["VBG", ["-", "describing", "improving", "using", "employing",  "according", "resulting", "having", "following", "including", "containing", "consisting", "disclosing"]  ] ] 
        #start_pat = [ ["NN", ["-", "method"]] ] 
        start_pat = []
        cont_pat = [ ["NN", []], ["VBN", []], ["IN", ["+", "of"]], ["DT",  []], ["CC", []], ["RP", []] ]
        end_pat = [ ["NN", []], ["NNP", []], ["NNS", []], ["NNPS", []], ["VBG", ["-", "describing", "improving", "using", "employing", "according", "resulting", "having", "following", "including", "containing", "consisting", "disclosing", "pertaining", "being", "comprising", "corresponding"]  ] ]
        start_pat.extend(both_pat)
        cont_pat.extend(both_pat)

    elif lang == "de":
        start_pat =  [ ["NN", []], ["NE", []], ["ADJA", []] ]
        cont_pat = [ ["NN", []], ["EN", []], ["ADJA", []], ["APPR", ["+", "von"]], ["ART", ["+", "des", "der"]] ]
        end_pat = [ ["NN", []], ["NE", []] ]

    elif lang == "cn":
        load_patterns = False
        if load_patterns:
            start_pat = []
            cont_pat = []
            end_pat = []
            fh = codecs.open("chunk_schema_%s.txt" % lang)
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                add_chunk_pattern_element(line, start_pat, cont_pat, end_pat)
        else:
            start_pat =  [ ["NN", []], ["NR", []], ["NT", []], ["JJ", []], ["VA", []] ]
            cont_pat = [ ["NN", []], ["NR", []], ["NT", []], ["JJ", []], ["VA", []], ["DEG", []], ["DEC", []] ]
            end_pat = [ ["NN", []]  ]
    
    cs = chunkSchema(start_pat, cont_pat, end_pat)
    return(cs)

# This is needed to deal with proper encoding of Chinese characters within chunk patterns
def add_chunk_pattern_element(line, start_pat, cont_pat, end_pat):
    (pattern_type, l_elements) = line.split("\t")
    l_elements = l_elements.split()
    tag = l_elements[0]
    constraint = l_elements[1:]
    if pattern_type == "start_pat":
        pattern_list = start_pat
    elif pattern_type == "cont_pat":
        pattern_list = cont_pat
    elif pattern_type == "end_pat":
        pattern_list = end_pat
    else:
        print "Warning: illegal pattern type"
        return
    pattern_list.append([tag, constraint])


def tag2chunk_dir(tag_dir, phr_occ_dir, phr_feats_dir, chunk_schema, year):
    #output_chunk = "/home/j/anick/fuse/data/patents/en_test/chunk/US20110052365A1.xml"
    for file in os.listdir(tag_dir):
        input = tag_dir + "/" + file
        output_phr_occ = phr_occ_dir + "/" + file
        output_phr_feats = phr_feats_dir + "/" + file

        doc = Doc(input, output_phr_occ, output_phr_feats, chunk_schema, year)

# tag2chunk.test_t2c()
def test_t2c():
    input = "/home/j/anick/fuse/data/patents/en_test/tag/US20110052365A1.xml"
    output_phr_occ = "/home/j/anick/fuse/data/patents/en_test/phr_occ/US20110052365A1.xml"
    output_phr_feats = "/home/j/anick/fuse/data/patents/en_test/phr_feats/US20110052365A1.xml"
    cs = chunk_schema("en")
    year = "1980"
    doc = Doc(input, output_phr_occ, output_phr_feats, cs, year)
    return(doc)

# tag2chunk.test_t2c_cn()
def test_t2c_cn():
    input = "/home/j/anick/fuse/data/patents/tmp/cn/CN1394959A-tf.tag"
    output_phr_occ = "/home/j/anick/fuse/data/patents/tmp/cn/CN1394959A-tf.phr_occ"
    output_phr_feats = "/home/j/anick/fuse/data/patents/tmp/cn/CN1394959A-tf.phr_feats"
    #chunk_schema = chunk_schema("cn")
    cs = chunk_schema("cn")
    #doc = Doc(input, output_phr_occ, output_phr_feats, chunk_schema)
    year = "1980"
    doc = Doc(input, output_phr_occ, output_phr_feats, cs, year)
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
    c_schema = chunk_schema(language)
    for year in os.listdir(tag_path):
        phr_occ_year_dir = phr_occ_path + "/" + year
        phr_feats_year_dir = phr_feats_path + "/" + year
        tag_year_dir = tag_path + "/" + year
        print "[patent_tag2chunk_dir]calling tag2chunk for dir: %s" % tag_year_dir
        tag2chunk_dir(tag_year_dir, phr_occ_year_dir, phr_feats_year_dir, c_schema, year)
    print "[patent_tag2chunk_dir]finished writing chunked data to %s and %s" % (phr_occ_path, phr_feats_path)

### debugging _no output produced PGA 10/8
def pipeline_tag2chunk_dir(root, language):
    
    phr_occ_path = root + "/phr_occ"
    phr_feats_path = root + "/phr_feats"
    tag_path = root + "/tag"
    c_schema = chunk_schema(language)
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
        doc = Doc(tag_file, output_phr_occ, output_phr_feats, c_schema, year)


    s_list.close()

    print "[pipeline_tag2chunk_dir]finished writing chunked data to %s and %s" % (phr_occ_path, phr_feats_path)


# top level call to tag txt data dir in a language
# tag2chunk.chunk_lang("en")
# tag2chunk.chunk_lang("de")
# tag2chunk.chunk_lang("cn")
def chunk_lang(lang):
    patent_path = "/home/j/anick/fuse/data/patents"
    patent_tag2chunk_dir("/home/j/anick/fuse/data/patents", lang)
