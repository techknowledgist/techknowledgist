
from lxml import etree
import os
import pdb

# stanford tagger
import sdp

# 
dir = "/home/j/clp/chinese/corpora/fuse-patents/500-patents/DATA/Lexis-Nexis/US/Xml/1980"
filename = "US4192770A.xml"


# NOTE:  This works only for English patents.
# The xml tags summary and claim-text are not used in Chinese or German docs.
class Patent:

    def __init__(self, dir, filename):
        ###print "[patent] entered init"
        # dict to map ids to objects                                                            
        self.dir = dir
        self.filename = filename
        self.path = dir + "/" + filename

        self.tree = None

        # load the annotation information from the xml file
        self.tree = self.xml_read_patent_file(self.path)

        self.biblio = self.tree.find("bibliographic-data")
        self.title = self.biblio.find("invention-title")
        self.abstract = self.tree.find("abstract").findall("p")[0]
        self.description = self.tree.find("description")
        self.summary = self.description.find("summary")
        # get everything in the description beside the summary element
        self.desc_rest = []

        # first claim
        self.claim_1 = self.tree.getroot().xpath("//claim-text")[0]
        
        for el in self.description:
            if el.tag != "summary":
                self.desc_rest.append(el) 
                

        self.lines = self.lines()

    # return a list of text lines, some indicating section headers of interest
    # The Stanford parser cannot handle lines over some length, so break up 
    # into sentences and trim lines if necessary here.

    def lines(self):
        lines = []
        line = "FH_TITLE:"
        txt = el_text(self.title)
        lines.append(line)

        lines.extend(txt)

        line = "FH_ABSTRACT:"
        txt = el_text(self.abstract)
        lines.append(line)
        lines.extend(txt)

        line = "FH_SUMMARY:"
        txt = el_text(self.summary)
        lines.append(line)
        lines.extend(txt)

        line = "FH_DESC_REST:"
        txt = el_text(self.desc_rest)
        lines.append(line)
        lines.extend(txt)

        line = "FH_CLAIM_1:"
        txt = el_text(self.claim_1)
        lines.append(line)
        lines.extend(txt)

        line = "\nEND:\n"
        lines.append(line)

        return(lines)

    def output_lines(self, output_file):
        s_out = open(output_file, "w")
        for line in self.lines:

            # make sure we can handle utf-8 characters
            uline = line.encode('utf-8')
            s_out.write("%s\n" % uline)

        s_out.close()

    def xml_read_patent_file(self, path):
        ###print "[xml_read_patent_file]path: %s" % (path)
        tree = etree.parse(path)
        root = tree.getroot()
        ###print "root: %s" % root
        #tags = root.find("TAGS")

        """
        l_xml_sectime = tags.findall("SECTIME")
        l_xml_event = tags.findall("EVENT")
        l_xml_timex3 = tags.findall("TIMEX3")
        l_xml_tlink = tags.findall("TLINK")

        for obj in l_xml_sectime:
            id = obj.get("id")
            start = obj.get("start")
            end = obj.get("end")
            text = obj.get("text")
            type = obj.get("type")
            dvalue = obj.get("dvalue")
        """

        return(tree)

# true if string contains only ws
def empty_sent_p(str):
    if str.lstrip() == "":
        return(True)
    else:
        return(False)

# break up a string into sentences
# Eliminate null "sentences" which sdp can't handle
def sents(str):
    l_sent = []
    u = 1  # ultimate char index
    p = 0  # penumltimate char index
    # next  subscript for end of sentence
    start = 0  # char index of start of current sentence in str
    next = 2
    last_space = 0
    max_sent_len = 80
    word_count = 0
    term_chars = [".", "!", "?"]
    sent = ""
    while u < len(str):
        #print "in while: u %i, p %i, start %i, next %i" % (u, p, start, next)
        next = u + 1

        # check for sent length overflow
        # but don't caunt multiple spaces as extra words
        if str[u] == " " and str[p] != " ":
            word_count += 1
            #print "word-count: %i" % word_count
            if word_count >= max_sent_len:
                # truncate sentence here
                # we have the end of a sentence
                ###print "[setns]in eos: u %i, p %i, start %i, next %i" % (u, p, start, next)
                # check for null sentence
                sent = str[start:next]
                sent = sent.strip()
                if sent != "":
                    ###print "[sents]Adding: |%s|" % sent
                    l_sent.append(sent)
                start = next
                word_count = 0

        # check for end of sentence
        if str[u] == "\n" or (str[u] == " " and str[p] in term_chars):
            ###print "in if: u %i, p %i, start %i, next %i" % (u, p, start, next)
            sent = str[start:next]
            sent = sent.strip()
            if sent != "":
                ###print "[sents]Adding: |%s|" % sent
                l_sent.append(sent)

            start = next
            word_count = 0
        u += 1
        p += 1


            
    # last sent
    if start != next:
        sent = str[start:next]
        sent = sent.strip()
        if sent != "":
            ###print "[sents]Adding: |%s|" % sent
            l_sent.append(sent)

    return(l_sent)
        


# takes a tree element or element list
# returns a list of text sections

def el_text(el_or_el_list):
    txt = []
    if type(el_or_el_list) != list:
        l_element = [ el_or_el_list ]
    else:
        l_element = el_or_el_list

    sentences = []
    for el in l_element:
        print "el: %s" % el
        # iterate over the elements within each sub section
        # split into sentences and trim length if necessary
        for e in el.iter(tag=etree.Element):
            if e.text != None:
                sentences = sents(e.text)
                txt.extend(sentences)

    return(txt)

def print_txt(txt):
    for line in txt:
        print line


# return all text in a section within the specified tag
def tree_text(section_root, tag=""):
    txt = ""
    if tag != "":
        l_element = section_root.findall(tag)
    else:
        l_element = section_root.iter(tag=etree.Element)

    for el in l_element:
        txt = txt + el.text + "  "

    return(txt)

# return individual text sections as separate list items
def tree_text_l(section_root, tag):
    txt = []
    l_element = section_root.findall(tag)
    
    for el in l_element:
        txt.append( el.text )

    return(txt)



def test():
    p1 = Patent(dir, filename)
    return(p1)

def els(subtree):

    for element in subtree.iter(tag=etree.Element):
        print("tag: %s\n%s" % (element.tag, element.text))


# output field\tNP\tleft_context\tright_context
# where left_context is 3 tokens
# right context is 1 token
def np_context(tag_file):
    s_tag = open(tag_file, "r")
    for line in s_tag:
        line = line.strip()
        
    s_tag.close()


#     # create a chunker schema instance and a tagger instance
#    cs = sdp.chunker_tech()
#    tagger = sdp.STagger("english-caseless-left3words-distsim.tagger") 

# output file includes full path
def process_patent_sent_file(patent_sent_dir, file_name, tagger, cs, output_file):
    debug_p = False
    s_patent = open(patent_sent_dir + "/" + file_name)
    s_output = open(output_file, "w")
    section = ""
    sent_no_in_section = 0
    for line in s_patent:
        line = line.strip("\n")
        
        if line[0:3] == "FH_":
            # we are at a section header
            section = line.split("_")[1]
            sent_no_in_section = 0
        else:
            if debug_p:
                print "[process_patent_sent_file]line: %s" % line
            # process the sentences in the section
            l_tag_string = tagger.tag(line)

            if debug_p:
                print "[process_patent_sent_file]l_tag_string: %s" % l_tag_string
            #print "ncontext:"
            #s1.ncontext()
            
            for tag_string in l_tag_string:
                
                sent = sdp.Sent(tag_string, cs)

                # get context info
                i = 0
                for chunk in sent.chunk_iter():
                    if chunk.label == "tech":
                        verb = sent.prev_V(i)
                        adj =  sent.prev_J(i)
                        head = sent.head_N(i)
                        hsent = sent.highlight_chunk(i)
                        if debug_p:
                            print "index: %i, start: %i, end: %i, sentence: %s" % (i, chunk.chunk_start, chunk.chunk_end, sent.sentence)
                        # this line contains some meta data (first 3 fields)
                        output_string =  file_name + "\t" + section + "\t" + str(sent_no_in_section) + "\t" + chunk.phrase + "\t" + verb + "\t" + adj + "\t" + sent.prev_n(chunk.chunk_start, 3) + "\t" + sent.next_n(chunk.chunk_end, 3) + "\t" + hsent + "\n" 
                        #print "%s\t%i|%s\t%s\t%s\t%s\t%s\t%s" % (section, sent_no_in_section, chunk.phrase,  verb, adj, sent.prev_n(chunk.chunk_start, 3), sent.next_n(chunk.chunk_end, 3), hsent)
                        # version without metadata
                        #output_string = chunk.phrase + "\t" + verb + "\t" + adj + "\t" + sent.prev_n(chunk.chunk_start, 3) + "\t" + sent.next_n(chunk.chunk_end, 3) + "\t" + hsent + "\n"
                        output_string = output_string.encode('utf-8')
                        #s_output.write( "%s\t%s\t%s\t%s\t%s\t%s" % (chunk.phrase,  verb, adj, sent.prev_n(chunk.chunk_start, 3), sent.next_n(chunk.chunk_end, 3), hsent))
                        s_output.write(output_string)
                        if debug_p:
                            print ""
                    i = chunk.chunk_end
                # keep track of the location of this sentence within the section
                sent_no_in_section += 1

    s_output.close()
    s_patent.close()


def process_patent_dir(patent_sent_dir, output_dir):
    # create a chunker schema instance
    cs = sdp.chunker_tech()
    # create tagger instance
    st = sdp.STagger("english-caseless-left3words-distsim.tagger") 

    # process each file in the dir
    for file_name in os.listdir(patent_sent_dir):
        output_file = output_dir + "/" + file_name
        process_patent_sent_file(patent_sent_dir, file_name, st, cs, output_file)

def test_ppd():
    patent_sent_dir = "/home/j/anick/fuse/data/patents/en/sent/1980"
    output_dir = "/home/j/anick/fuse/data/patents/en/tag/1980"
    process_patent_dir(patent_sent_dir, output_dir)

def test_pm():
    dir = "/home/j/anick/fuse/data/pubmed"
    file = "pubmed_lines.txt"
    output_file = "/home/j/anick/fuse/data/pubmed/chunks.txt"
    #file = "pubmed_lines_test_1.txt"
    # create a chunker schema instance
    cs = sdp.chunker_tech()
    # create tagger instance
    tagger = sdp.STagger("english-caseless-left3words-distsim.tagger") 

    process_patent_sent_file(dir, file, tagger, cs, output_file)


"""
# process file generated by Olga from pubmed titles and abstracts
def process_pubmed_lines_file(pubmed_file, tagger, cs):
    s_pm = open(pubmed_file)
    for line in s_pm:
        line= line.strip("\n")
        fields = line.split("\t")
        
    s_pm.close()
"""
