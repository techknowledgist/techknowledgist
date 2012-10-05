# i2b2
# utilities for i2b2

import os, glob, re, sys
import utils
import pickle
import types
import re
import i2b2_config

# stanford parser routines
import sdp

# debugger
import pdb

# set to True to output a log of dates assigned to each line of text
log_date_p = False
# log_date_p = True

# Date functions (from Nianwen Xue 6/29/11)
# NOTE: PGA changed name of parse(date) to parse_date(date) to avoid confusion  (change both def and call)
# updated 7/18/11 from new_extract_dates.py from Bert to handle UPitt dates in the form
# **DATE[Nov 18 2007]

# regular expressions
date_pat = re.compile(r'\d+[-/]\d+[-/]\d*')
mon_pat = re.compile(r'((January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec) *\d* *\,? *\d*)')

# time frame based on words appearing in field names
# "present" trumps "history" if both appear in same field
tf_present_terms = ["present", "hpi"]
tf_family_terms = ["family"]
tf_past_terms = ["past", "history", "psychosocial", "social", "pmh", "psh"]
tf_discharge_terms = ["discharge", "discharged", "final", "transfer"]
tf_instructions_terms = ["followup", "follow", "plan", "instruction", "instructions", "follow-up", "recommendation", "recommendations"]
tf_anytime_terms = ["allergies", "habits"]
tf_exam_terms = ["exam", "exams", "examination", "examinations", "lab", "labs", "test", "tests", "laboratory", "result", "results"]

# takes a list of lower case tokens for a field and returns a letter indicating temporal type.
def get_time_frame(l_lc_tokens):
    if utils.intersect(l_lc_tokens, tf_family_terms) != []:
        # field refers to people in patient's family
        return "F"
    elif utils.intersect(l_lc_tokens, tf_present_terms) != []:
        # field refers to present time (regardless of word history in same field name)
        return "C"
    elif utils.intersect(l_lc_tokens, tf_past_terms) != []:
        # field refers to past medical or social history
        return "P"
    elif utils.intersect(l_lc_tokens, tf_discharge_terms) != []:
        # field refers to state at discharge
        return "D"
    elif utils.intersect(l_lc_tokens, tf_instructions_terms) != []:
        # field refers to instructions after discharge
        return "I"
    elif utils.intersect(l_lc_tokens, tf_anytime_terms) != []:
        # field refers to things unlikely to change over time
        return "A"
    elif utils.intersect(l_lc_tokens, tf_exam_terms) != []:
        # field refers to reporting test results
        return "E"
    
    else:
        # default to "unknown time"
        return "U"

def get_line_date(line):
    """scans a line to find dates"""
    dates = filter_date(date_pat.findall(line) + mon_pat.findall(line, re.I))
    if len(dates) > 0:
        return parse_date(dates[0])
    return ''

def filter_date(lst):
    """filter out some fake dates such as 555-95-9320"""
    
    final_list = []
    for item in lst:
        if isinstance(item, tuple):
            final_list.append(item[0])
        else:
            item = item.replace('/', '-') 
            parts = item.split('-')
            include = True
            for part in parts:
                if not(len(part) == 1 or len(part) == 2 or len(part) == 4):
                    include = False
            if include:
                final_list.append(item)
    return final_list

        

def parse_date(date):
    """parse a date into numerical format"""
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    months2 = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    mon_digits = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
    month_dict = dict(zip(months, mon_digits))
    month_dict2 = dict(zip(months2, mon_digits))
    parts = date.split()
    if len(parts) <= 1:
        return date
    parts1 = filter(lambda a: a != ',', parts)
    parts2 = []
    for p in parts1:
        if p in month_dict:
            parts2.append(month_dict[p])
        elif p in month_dict2:
            parts2.append(month_dict2[p])
        else:
            parts2.append(p)
    return '-'.join(parts2)
    

    

def get_doc_date(path):
    """given a file, return the admission date or the first date in the document"""
    fh = open(path)
    #date_pat = re.compile(r'\d+[-/]\d+[-/]\d*')
    first_date = ''
    admission = False
    
    for line in fh.readlines():
        if re.search("admission date *\:",line, re.I) or re.search('Admitted *\:', line, re.I):
            admission = True
        date = get_line_date(line)
        if date != '':
            if admission:
                return date
            if first_date == '':
                first_date = date
    fh.close()
    return first_date
        
# parsing annotated data

# create a key from doc_id and doc_line_no
def doc_line2key(doc_id, doc_line_no):
    return(doc_id + "_" + str(doc_line_no))

def get_np_head(token_list):
    # We don't really handle these cases well:
    # ck 's
    # part 1 of a sleep study
    # (fully parenthesized)
    splitters = ("with", "of", "for", "in", "on", "between", "above", "below", "within", "without", "to", "(", "greater", "less", "from", "at", "toward", "towards", "behind", "among", "about", ")" ) 

    # heuristic: return the last token unless 
    # there is a splitter in some location other than 0.
    # If there is a splitter and it is not token 0, then return the 
    # token before the splitter.

    tl_last_index = len(token_list) - 1
    # set default head
    head = token_list[tl_last_index]
    # check for splitters to reassign head
    i = 0
    token = token_list[i]
    while token not in splitters and i <= tl_last_index:
        #pdb.set_trace()
        head = token
        i += 1
        if i <= tl_last_index:
            token = token_list[i]
    return(head)


class Txt:

    # class variable to assign corpus wide integer to each created instance
    next_no = 0

    # Heuristically classify text lines into
    # field: a line terminating in a colon
    # short: a line of short_length or fewer tokens (also likely a field name
    #        or non-NLP value
    # long: non-field line longer than short_length tokens
    # over: line longer than max_length tokens (not sent to Stanford parser, w/max 100 tokens)

    # last_field_name is the most recently encountered line that ends in a colon
    # last_time_frame is the time frame as determined from the last field name encountered
    def __init__(self, line, doc_id, doc_line_no, last_field_name, last_field_line_no, last_time_frame):
        short_length = 3
        max_length = 50
        line = line.strip("\n")
        self.doc_line_no = doc_line_no
        self.field = string2symbol(last_field_name)
        # we will set last_field_line_no in process_txt_dir
        self.last_field_line_no = 0
        # Assign the global instance no
        self.no = Txt.next_no
        Txt.next_no += 1
        self.doc_id = doc_id
        self.line = utils.restore_line_punc(line)
        self.lc_line = self.line.lower()
        self.tokens = self.line.split()
        self.lc_tokens = self.lc_line.split()
        # date if one is found in the line. Otherwise it stays the empty string ""
        self.date = ""
        self.time_frame = last_time_frame

        # test for an empty line.  This shouldn't occur but does occasionally.
        # An empty line still counts as a line in the numbering scheme for concepts, so we
        # can't just ignore it.
        if line != "":

            # if line ends in ":", it is probably a field
            if line[-1] == ":":
                self.type = "field"
                # determine the time_frame (time frame) for lines in this field
                self.time_frame = get_time_frame(self.lc_tokens)
            
            elif len(self.tokens) <= short_length:
                self.type = "short"
            elif len(self.tokens) <= max_length:
                self.type = "long"
            else:
                self.type = "over"
        else:
            # empty line
            self.type = "short"

    def display(self):
        print "[txt] no: %i, doc: %s, line_no: %i, type: %s, line: %s" % (self.no, self.doc_id, self.doc_line_no, self.type, self.line)

        # linear form of key data for output to an external file
    def txt2file_format(self):
        line = "txt " + str(self.no) + " " + self.doc_id + " " + str(self.doc_line_no) + "\t\t" + self.line 
        return(line)

    

class Subtxt:

    # class variable to assign corpus wide integer to each created instance
    # will be taken from the corresponding txt instance rather than generated
    # independently

    def __init__(self, txt_no, doc_id, doc_line_no, field):
        self.doc_id = doc_id
        self.doc_line_no = doc_line_no
        self.tokens = []
        self.line = ""
        self.field = field
        # Assign the global instance no
        self.no = txt_no


    def display(self):
        print "[subtxt] no: %i, doc_id: %s, doc_line_no: %i, line: %s" % (self.no, self.doc_id, self.doc_line_no, self.line)

        # linear form of key data for output to an external file
    def subtxt2file_format(self):
        line = "subtxt " + str(self.no) + " " + self.doc_id + " " + str(self.doc_line_no) + "\t\t" + self.line 
        return(line)


class Subcon:


    # token_counter is sequential integer used as part of the name of the subcon instance
    # (TYPE_COUNTER)
    def __init__(self, con_no, con_id, type, token_counter, doc_id, line_start, con_head):
        self.con_id = con_id
        self.type = type
        self.doc_id = doc_id
        self.line_start = line_start
        self.txt_no = -1
        self.loc = -1

        # 5/18/10 PGA moved the token creation into a method to allow us
        # to try different strategies.
        self.token = self.make_subcon_token(con_head, token_counter)
        self.loc = -1
        # Assign the global instance no to be same as con.no
        self.no = con_no

    
    # A subcon token replaces a phrase of known type in the 
    # original txt.  The idea is to create a simpler sentence
    # for the parser to try to parse.  However, since the parser is
    # sensitive to inividual words, we have to choose words that are
    # more likely to mimic the behavior of the phrases they replace.
    # So problem can be adjectival (She was x) or nominal (She had x).
    # Treatment can take a det or not and is only a noun.
    # Exam 
    def make_subcon_token(self, token, token_counter):
        """
        # Original strategy was the following
        # token will be uppercased concept_type plus a counter digit 
        # token = type.upper() + "_" + str(token_counter)
        # 
        # Changed to a strategy leaving out the token_counter and 
        # using uppercased words that are always nouns, in case the parser
        # uses knowledge of the word in its parsing.  We replace type "test"
        # with "exam" since "exam" is not a possible verb.
        if type == "test":
            token = "exam"
        elif type == "problem":
            # we choose a word that can be both noun and adjective complement, since
            # problems can be both np's and adjective phrases
            token = "hostile"
        elif type == "treatment":
            token = "treatment"
        # add the token_counter to make the string unique
        # a condition of the code that reassigns the locations of the subcons.
        """
        subtoken =  token + "__" + str(token_counter)
        return(subtoken)



    def display(self):
        print "[subcon] no: %i, con_id: %s, token: %s, txt_no: %i " % (self.no, self.con_id, self.token, self.txt_no)

    # linear form of key data for output to an external file
    def subcon2file_format(self):
        line = "subcon " + str(self.no) + " " + self.type + " " + self.doc_id + " " + str(self.line_start) + " " + str(self.txt_no) + "\t\t" + self.token + "\t" + str(self.loc) 
        return(line)

# create a unique id for a concept instance
# used in annotations.d_con as key
def make_con_id(doc_id, line_start, token_start, line_end, token_end):
    con_id = doc_id + "_" + line_start + "_" + token_start + "_" + line_end + "_" + token_end
    return con_id

def make_con_sort_id(line_start, token_start, line_end, token_end):
    con_sort_id = ((line_start * 10000) + token_start) * 10000 + int(token_end)
    
    """
    con_sort_id = line_start * 10000
    print "[make_con_sort_id] con_sort_id: %s" % con_sort_id
    con_sort_id = con_sort_id + token_start
    print "[make_con_sort_id] con_sort_id: %s" % con_sort_id
    con_sort_id = con_sort_id * 10000
    print "[make_con_sort_id] con_sort_id: %s" % con_sort_id
    con_sort_id = con_sort_id + token_end
    print "[make_con_sort_id] con_sort_id: %s" % con_sort_id
    pdb.set_trace()
    """
    return(con_sort_id)

# given a string which might contain blanks, replace all blanks with 
# delim (_ as default).  This is useful when the string needs to be
# used as a symbol or feature in a blank separated file.
def string2symbol(string, delim = "_"):
    string = re.sub(" ", delim, string) 
    return string


def get_con_fields(con_info):
    # note we have to split carefully since the string can contain blanks                             
    # The data has cases like:                                                                        
    # c="" pin placement " in left foot" 35:3 35:9                                                    
    # So we can't just use '" ' as a field separator                                                  
    # (string_info, loc_info) = con_info.split('" ')                                                   
    split_loc = con_info.rfind('" ')
    string_info = con_info[0:split_loc]
    loc_info = con_info[split_loc + 2:]
    return([string_info, loc_info])

# con file
# lines are of the form:
# c="flexeril drug" 39:5 39:5||t="treatment"
# concept line:token_start line:token_end || type
# no is sequential integer id.
class Con:
    # class variable to assign corpus wide integer to each created instance
    next_no = 0

    # extract fields from line in .con file
    def __init__(self, line, doc_id):
        line = line.strip("\n")
        self.line = line
        (con_info, type_info) = line.split("||")
        # print "[con] con_info: %s, type_info: %s" % (con_info, type_info)
        # note we have to split carefully since the string can contain blanks
	# The data has cases like:
        # c="" pin placement " in left foot" 35:3 35:9
        # So we can't just use '" ' as a field separator                                               
        (string_info, loc_info) = get_con_fields(con_info)

        # Assign the global instance no
        self.no = Con.next_no
        Con.next_no += 1

        # pointer to previous con in text.  This will be set by CorefData.gen_cand_pairs in cnlp module.
        self.prev_con = None

        (start_info, end_info) = loc_info.split()
        # string as it appears in i2b2 source record
        self.original_string = string_info[3:]
        # string adusted so that punc characters appear as natural punc
        self.string = utils.restore_line_punc(string_info[3:])
        self.symbol = string2symbol(self.string)
        self.tokens = self.string.split()
        (line_start, token_start) = start_info.split(":")
        (line_end, token_end) = end_info.split(":")
        self.line_start = int(line_start)
        self.line_end = int(line_end)
        self.token_start = int(token_start)
        self.token_end = int(token_end)
        self.doc_id = doc_id
        self.con_id = make_con_id(doc_id, line_start, token_start, line_end, token_end)
        # sort_id is unique within document and usable to sort concepts by order within document
        #pdb.set_trace()
        self.sort_id = make_con_sort_id(self.line_start, self.token_start, self.line_end, self.token_end)
        
        self.type = type_info[3:-1]
        # head word
        self.head = get_np_head(self.tokens)

        # numberic id of txt instance (to be added later)
        self.txt_no = -1

    # linear form of key data for output to an external file
    def con2file_format(self):
        line = "con " + str(self.no) + " " + self.type + " " + self.doc_id + " " + str(self.line_start) + " " + str(self.txt_no) + "\t\t" + self.string + "\t" + str(self.token_start) + "\t" + str(self.token_end)
        return(line)

    def attrs2line(self):
        line = self.type +  "\t" + str(self.no) + "\t" + str(self.txt_no) + "\t" + self.doc_id + "\t" + str(self.line_start) + "\t" + self.symbol + "\t" + self.string + "\t" + str(self.token_start) + "\t" + str(self.token_end) 
        return(line)

    # returns an ordered list of feature values
    def features(self):
        l_features = [self.symbol, self.type, self.line_start, self.token_start, self.line_end, self.token_end]
        return(l_features)
        
    def display(self):
        print "[con]no: %i, string: %s, line_start: %i, token_start: %i, line_end: %i, token_end: %i, type: %s, txt_no: %i" % (self.no, self.string, self.line_start, self.token_start, self.line_end, self.token_end, self.type, self.txt_no)

    def inspect(self):
        print "[CON] %s: %s (txt %i)" % (self.type, self.string, self.txt_no )

    # not working
    # returns txt instance this concept appears in
    # fixed 7/17/11 PGA?
    def get_txt(self, annot):
        txt = annot.d_txt_no.get(self.txt_no)
        return(txt)
    
    # not working? Obsolete now that you can get txt_no from con instance directly.  7/7/11 PGA
    # returns the txt number for the given annotation
    def get_txt_no(self, annot):
        txt = annot.d_txt_no.get(self.txt_no)
        return txt.no


class Doc:
    def __init__(self, doc_id):
        self.doc_id = doc_id
        self.l_sorted_concepts = []
        self.l_txt = []
        self.d_con_sort_id2con = {}
        # map a concept id into its position in the list of sorted concepts for the doc
        self.d_con_id2sort_index = {}
        
    def sort_concepts(self):
        #print "at 0. current_chain: %s" % current_chain
        # sort the chain by converting cid to lt_no
        #pdb.set_trace()
        l_sort_ids = []

        # l_sorted_concepts is not sorted yet, just
        # a list of all concepts found in this doc
        for con in self.l_sorted_concepts:
            l_sort_ids.append(con.sort_id)
            self.d_con_sort_id2con[con.sort_id] = con
            
        l_sort_ids.sort()

        # now map the sorted id list back into a sorted con list
        l_sorted_cons = []
        for sort_id in l_sort_ids:
            con = self.d_con_sort_id2con.get(sort_id)
            l_sorted_cons.append(con)
        #print "at 2.  sorted_con_chain: %s" % sorted_con_chain
        # replace doc's unsorted list with sorted list
        self.l_sorted_concepts = l_sorted_cons
        # generate mapping from con.no to position in sorted concept list
        i = 0
        #pdb.set_trace()
        for scon in self.l_sorted_concepts:
            self.d_con_id2sort_index[scon.no] = i
            i+= 1

    # given a concept id, find the closest preceding concept of the same type
    # Returns None if none found
    def concept_antecedent(self, con):
        antecedent_found_p = False
        # start looking for antecedents in sorted concept list,
        # working backwards from the current concept's position
        sort_index = self.d_con_id2sort_index.get(con.no) - 1
        while antecedent_found_p == False and sort_index > 0:
            prior_con = self.l_sorted_concepts[sort_index]
            if prior_con.type == con.type:
                return(prior_con)
            else:
                sort_index = sort_index - 1
        return(None)

# ast file
# lines are of the form:
# c="left shoulder / neck strain / sprain" 37:0 37:6||t="problem"||a="present"
# concept line:token_start line:token_end || type || assertion
# no is sequential integer id.
class Ast:
    # class variable to assign corpus wide integer to each created instance
    next_no = 0

    # extract fields from line in .ast file
    def __init__(self, line, doc_id):
        line = line.strip("\n")
        (con_info, type_info, assert_info) = line.split("||")
        # print "[ast] con_info: %s, type_info: %s, assert_info: %s" % (con_info, type_info, assert_info)
        # note we have to split carefully since the string can contain blanks
        (string_info, loc_info) = get_con_fields(con_info)

        # Assign the global instance no
        self.no = Ast.next_no
        Ast.next_no += 1
        
        (start_info, end_info) = loc_info.split()
        self.string = utils.restore_line_punc(string_info[3:])
        self.symbol = string2symbol(self.string)
        (line_start, token_start) = start_info.split(":")
        (line_end, token_end) = end_info.split(":")
        self.line_start = int(line_start)
        self.line_end = int(line_end)
        self.token_start = int(token_start)
        self.token_end = int(token_end)
        self.con_id = make_con_id(doc_id, line_start, token_start, line_end, token_end)
        self.doc_id = doc_id

        self.type = type_info[3:-1]
        self.ast = assert_info[3:-1]
        # make sure final " is removed
        # In some cases, without the line below, the quote remained
        self.ast = self.ast.strip('"')

        # numeric id of txt instance (to be added later)
        self.txt_no = -1

    # linear form of key data for output to an external file
    def ast2file_format(self):
        line = "ast " + str(self.no) + " " + self.ast + " " + self.doc_id + " " + str(self.line_start) + " " + str(self.txt_no) + "\t\t" + self.string + "\t" +  self.type + "\t" + str(self.token_start) + "\t" + str(self.token_end)
        return(line)

    def attrs2line(self):
        line = self.ast + "\t" + str(self.no) + "\t" + str(self.txt_no) + "\t" + self.doc_id + "\t" + str(self.line_start) + "\t" + self.symbol + "\t" + self.string + "\t" + self.type + "\t" + str(self.token_start) + "\t" + str(self.token_end) 
        return(line)

    # returns an ordered list of feature values
    def features(self, annot):
        # fetch the types of each concept
        con = annot.d_con_id.get(self.con_id)
        l_features = [self.ast, self.symbol, con.type, self.line_start, self.token_start, self.line_end, self.token_end]
        return(l_features)

    def display(self):
        print "[ast]no: %i, string: %s, line_start: %i, token_start: %i, line_end: %i, token_end: %i, type: %s, ast: %s" % (self.no, self.string, self.line_start, self.token_start, self.line_end, self.token_end, self.type, self.ast)

    def inspect(self, stream = ""):
        if stream == "":
            print "[AST] %s: %s | %s (txt %i)" % (self.type, self.string, self.ast, self.txt_no)
        else:
            stream.write("[AST] %s: %s | %s (txt %i)" % (self.type, self.string, self.ast, self.txt_no))


    # returns txt instance this concept appears in 
    def get_txt(self, annot):
        doc = annot.d_doc.get(self.doc_id)
        txt = doc.get_txt_at_line(self.line_start)
        return(txt)

    # returns the txt number for the given annotation
    def get_txt_no(self, annot):
        doc = annot.d_doc.get(self.doc_id)
        txt = doc.get_txt_at_line(self.line_start)
        return txt.no

# rel file
# lines are of the form:
# c="duoneb ( albuterol and ipratropium nebulizer )" 35:49 35:55||r="TrAP"||c="wheezing" 35:70 35:70
# concept line:token_start line:token_end || relation || concept etc.
# no is sequential integer id.
class Rel:
    # class variable to assign corpus wide integer to each created instance
    next_no = 0

    # extract fields from line in .rel file
    def __init__(self, line, doc_id):
        line = line.strip("\n")
        (con1_info, rel_info, con2_info) = line.split("||")
        # print "[rel] con1_info: %s, rel_info: %s, con2_info: %s" % (con1_info, rel_info, con2_info)
        # note we have to split carefully since the string can contain blanks
        #(string_info, loc_info) = con1_info.split('" ')
        (string_info, loc_info) = get_con_fields(con1_info)

        (start_info, end_info) = loc_info.split()

        # Assign the global instance no
        self.no = Rel.next_no
        Rel.next_no += 1


        self.doc_id = doc_id
        # print "[rel]c1 string_info: %s, loc_info: %s" % (string_info, loc_info)
        self.c1_string =  utils.restore_line_punc(string_info[3:])
        self.c1_symbol = string2symbol(self.c1_string)
        (line_start, token_start) = start_info.split(":")
        (line_end, token_end) = end_info.split(":")
        self.c1_line_start = int(line_start)
        self.c1_line_end = int(line_end)
        self.c1_token_start = int(token_start)
        self.c1_token_end = int(token_end)
        self.c1_id = make_con_id(doc_id, line_start, token_start, line_end, token_end)

        # numeric id of txt instance (to be added later)
        self.txt_no = -1

        self.rel = rel_info[3:-1]

        # parse the second concept
        # note we have to split carefully since the string can contain blanks
        # can't use this: (string_info, loc_info) = con2_info.split('" ')
        (string_info, loc_info) = get_con_fields(con2_info)
        (start_info, end_info) = loc_info.split()

        # print "[rel]c2 string_info: %s, loc_info: %s" % (string_info, loc_info)
        self.c2_string =  utils.restore_line_punc(string_info[3:])
        self.c2_symbol = string2symbol(self.c2_string)
        (line_start, token_start) = start_info.split(":")
        (line_end, token_end) = end_info.split(":")
        self.c2_line_start = int(line_start)
        self.c2_line_end = int(line_end)
        self.c2_token_start = int(token_start)
        self.c2_token_end = int(token_end)
        self.c2_id = make_con_id(doc_id, line_start, token_start, line_end, token_end)
        
        # type gets instantiated later after all cons have been processed
        # since we get the type from the con instances
        self.c1_type = ""
        self.c2_type = ""

        # ast gets instantiated later after all cons have been processed
        # since we get the type from the ast instances
        # Note ast only applies if concept is of type "problem"
        self.c1_ast = ""
        self.c2_ast = ""

        # subline info to map c1 and c2 to their respective pseudoconcepts in subline
        # Since the pseudoconcepts are single tokens, we only need the start locations
        # ///PGA Need to implement these!
        self.c1_subline_start = 0
        self.c2_subline_start = 0
        self.c1_subline_token = ""
        self.c2_subline_token = ""

    # create an i2b2 record for this rel, inserting pred as the value of class in  r=<class>
    def i2b2_format_pred(self, pred):

        rel_record = "c=\"" + self.c1_string + "\" " + str(self.c1_line_start) + ":" + str(self.c1_token_start) + " " + str(self.c1_line_end) + ":" + str(self.c1_token_end) + "||r=\"" + pred + "\"||c=\""  + self.c2_string + "\" " + str(self.c2_line_start) + ":" + str(self.c2_token_start) + " " + str(self.c2_line_end) + ":" + str(self.c2_token_end)

        return(rel_record)



    # returns an ordered list of feature values
    def features(self, annot):
        # fetch the types of each concept
        c1 = annot.d_con_id.get(self.c1_id)
        c2 = annot.d_con_id.get(self.c2_id)
        l_features = [self.rel, self.c1_symbol, c1.type, self.c1_line_start, self.c1_token_start, self.c1_line_end, self.c1_token_end, self.c2_symbol, c2.type, self.c2_line_start, self.c2_token_start, self.c2_line_end, self.c2_token_end]
        return(l_features)

    # returns the line of text this relation came from
    def get_line(self, annot):
        doc = annot.d_doc.get(self.doc_id)
        txt = doc.get_txt_at_line(self.c1_line_start)
        return txt.line

    # returns txt instance this concept appears in 
    def get_txt(self, annot):
        doc = annot.d_doc.get(self.doc_id)
        txt = doc.get_txt_at_line(self.line_start)
        return(txt)

    # returns the txt number for the given annotation
    def get_txt_no(self, annot):
        doc = annot.d_doc.get(self.doc_id)
        txt = doc.get_txt_at_line(self.c1_line_start)
        return txt.no

    # linear form of key data for output to an external file
    def rel2file_format(self):
        line = "rel " + str(self.no) + " " + self.rel + " " + self.doc_id + " " + str(self.c1_line_start) + " " + str(self.txt_no) + "\t\t"  + self.c1_string + "\t" +  self.c1_type + "\t" + self.c1_ast + "\t" + str(self.c1_token_start) + "\t" + str(self.c1_token_end)  + "\t" + self.c2_string + "\t" +  self.c2_type + "\t" + self.c2_ast + "\t" + str(self.c2_token_start) + "\t" + str(self.c2_token_end)
        return(line)

    def attrs2line(self):
        line = self.rel + "\t" + str(self.no) + "\t" + str(self.txt_no) + "\t" + self.doc_id + "\t" + str(self.c1_line_start) + "\t" + self.c1_symbol + "\t" + self.c1_string + "\t" + self.c1_type + "\t" + self.c1_ast_type + "\t" + str(self.c1_token_start) + "\t" + str(self.c1_token_end) + "\t"  + self.c2_symbol + "\t" + self.c2_string + "\t" + self.c2_type + "\t" + self.c2_ast_type + "\t" + str(self.c2_token_start) + "\t" + str(self.c2_token_end) 
        return(line)

    # subrel is same info as rel except we are using the pseudoconcepts and subline
    # we need the concept ids and their locations in the subline
    def attrs2line_subrel(self):
        line = self.rel + "\t" + str(self.no) + "\t" + str(self.txt_no) + "\t" + self.doc_id + "\t" + str(self.c1_line_start) + "\t" + self.c1_symbol + "\t" + self.c1_string + "\t" + self.c1_type + "\t" + self.c1_ast_type + "\t" + str(self.c1_token_start) + "\t" + str(self.c1_token_end) + "\t"  + self.c2_symbol + "\t" + self.c2_string + "\t" + self.c2_type + "\t" + self.c2_ast_type + "\t" + str(self.c2_token_start) + "\t" + str(self.c2_token_end) 
        return(line)


    def display(self):
        print "[rel]c1_string: %s, c1_id: %s, c1_line_start: %i, c1_token_start: %i, c1_line_end: %i, c1_token_end: %i, rel: %s, c2_string: %s, c2_id: %s, c2_line_start: %i, c2_token_start: %i, c2_line_end: %i, c2_token_end: %i, txt_no: %i" % (self.c1_string, self.c1_id, self.c1_line_start, self.c1_token_start, self.c1_line_end, self.c1_token_end, self.rel, self.c2_string, self.c2_id, self.c2_line_start, self.c2_token_start, self.c2_line_end, self.c2_token_end, self.txt_no)

    def inspect(self, stream = ""):
        if stream == "":
            print "[REL] %s (%s: %s |%s: %s) (txt %i)" % (self.rel, self.c1_type, self.c1_string, self.c2_type, self.c2_string, self.txt_no)
        else:
            stream.write("[REL] %s (%s: %s |%s: %s) (txt %i)" % (self.rel, self.c1_type, self.c1_string, self.c2_type, self.c2_string, self.txt_no))

    def inspect2stream(self, stream = ""):
        if stream == "":
            print "[REL] %s (%s: %s |%s: %s) (txt %i)" % (self.rel, self.c1_type, self.c1_string, self.c2_type, self.c2_string, self.txt_no)
        else:
            stream.write("[REL] %s (%s: %s |%s: %s) (txt %i)" % (self.rel, self.c1_type, self.c1_string, self.c2_type, self.c2_string, self.txt_no))



class Annotations:
    
    def __init__(self):

        # lists of all con, ast, rel instances
        self.l_con = []
        self.l_ast = []
        self.l_rel = []
        self.l_txt = []
        self.l_subtxt = []
        self.l_subcon = []
        self.l_docid = []

        # dict indexed by sequential number, starting at 0
        self.d_con_no = {}
        self.d_ast_no = {}
        self.d_rel_no = {}
        self.d_txt_no = {}
        self.d_subcon_no = {}
        # retrieve subtxt with txt_no
        self.d_txt_no2subtxt = {}
        self.d_doc_id2doc = {}

        # given txt_no returns a list of con instances
        # Checking the txt_no entries in this file is a convenient way
        # of identifying txt lines that contain a concept
        self.d_txt_no2con_list = {}
        self.d_txt_no2subcon_list = {}
        # dict of concepts indexed by con_id
        # con_id is <doc_id>_<line_start>_<token_start>_<line_end>_<token_end>
        self.d_con_id = {}
        # given a con_id, returns an ast instance
        self.d_con_id2ast = {}
        # relate con and subcon through con_id
        # key is con_id, value is subcon
        self.d_con_id2subcon = {}
        self.d_con_no2subcon = {}
        # we can fetch the respective con using the con_id value in a subcon.

        # map from doc_id and line to corpus txt_no
        self.d_docline2txt_no = {}
        # map from doc_id and line to corpus txt
        self.d_docline2txt = {}
        # dict of assertions indexed by con_id
        self.d_con_id2ast = {}
        
        # dict of parsed sentences
        self.d_txt_no2pline = {}
        
        # lexicon of surface and lemma forms
        self.d_lex = {}

        # dict mapping doc_id to list of concepts in the doc
        self.d_docid2con_list = {}

    # create a profile string to illustrate the nature of the concepts within the 
    # sentence.  Take the concepts in order and output the chars {p (problem), t (test), r (treatment)}
    # to create the profile.  We could train separately on different profiles.
    def txt_profile(self, txt_no):
        profile = ""
        con_list = self.d_txt_no2con_list.get(txt_no)
        type_list = []
        for con in con_list:
            type = con.type
            loc = con.token_start
            type_list.append([loc, type])
        type_list.sort(utils.list_element_1_sort)
        for type_item in type_list:
            if type_item[1] == "problem":
                type_char = "p"
            elif type_item[1] == "test":
                type_char = "t"
            else: 
                # treatment
                type_char = "r"

            profile = profile + type_char
        return(profile)

    def process_lexicon(self, full_file_name):
        # lexicon should be loaded before creating chart instances
        s_lex = open(full_file_name, "r")
        for line in s_lex:
            line = line.strip("\n")
            line = line.strip(" ")
            (surface, lemma, pos, pos_detailed, paradigm_info) = line.split()
            # key is pos <underscore> surface form
            # pos: verb, noun, conjunction, preposition, adjective, adverb
            key = pos + "_" + surface
            self.d_lex[key] = lemma
        s_lex.close()

    def process_txt_dir(self, path):
        print "[annotations process_txt_dir]path: %s" % path

        if log_date_p:
            mallet_dir = i2b2_config.mallet_dir
            date_log_file = mallet_dir + "date_log.txt"
            s_date_log = open(date_log_file, "w")

        file_type_wildcard = "*.txt"
        type_path = path + "txt"
        if not os.path.exists(type_path):
            print "Error: path %s does not exist" % type_path
            print "Make sure the directory containing this annotation type has this name"
            sys.exit()

        last_field_name = "_none_"
        for infile in glob.glob( os.path.join(type_path, file_type_wildcard) ):
            # 8/23/11 changing the way we handle dates.
            # If line contains an explicit date, we keep it.  Otherwise date is "" for unknown
            # doc_date is the admission date or first date in the document (or "" if none)
            # doc_date = get_doc_date(infile)
            doc_id = utils.path2filename(infile, 0)
            # create Doc instance
            new_doc = Doc(doc_id)
            self.l_docid.append(doc_id)
            self.d_doc_id2doc[doc_id] = new_doc
            #print "[process_txt_dir] doc_id: %s" % doc_id
            stream = open(infile, 'r')
            doc_line_no = 1
            # track the line no corresponding to the start of the current field
            # This is useful to know which lines are in the same field as the current line.
            last_field_line_no = 1
            # default time frame is "current"
            last_time_frame = "C"
            
            # by default, if line does not contain a date, we choose the line_date as
            # (1) the previous date mentioned in the same field or
            # (2) the doc_date
            # line time frame is the time frame indicated by the contents of the current field name

            for line in stream:

                new_txt = Txt(line, doc_id, doc_line_no, last_field_name, last_field_line_no, last_time_frame)
                new_doc.l_txt.append(new_txt)
                # if the txt line ends in a colon, treat it as a field for subsequent line(s)
                if new_txt.type == "field":
                    last_field_name = new_txt.line
                    last_field_line_no = doc_line_no
                    last_time_frame = new_txt.time_frame
                    # line_date = doc_date

                # See if line contains a date
                # If not, use the default ""
                new_line_date = get_line_date(line)
                if new_line_date != "":
                    new_txt.date = new_line_date

                if log_date_p:
                    s_date_log.write(str(doc_line_no) + " " + str(last_field_line_no)  + " [" + last_time_frame + " " + new_line_date + "] " + line.lower() + "\n")
                
                new_txt.last_field_line_no = last_field_line_no
                #print "[process_txt_dir] new_txt no: %i" % new_txt.no
                self.l_txt.append(new_txt)
                self.d_txt_no[new_txt.no] = new_txt
                doc_line_key = doc_line2key(doc_id, doc_line_no)
                self.d_docline2txt_no[doc_line_key] = new_txt.no
                self.d_docline2txt[doc_line_key] = new_txt
                doc_line_no += 1
            stream.close()

        if log_date_p:
            s_date_log.close()


    """
    * Load cons
    make con_no (sequential)
    make con_no => Con
    make con_id 
    make con_id => Con
    make l_con
    add txt_no (via doc_id+line => txt_no)
    make txt_no => con
    """
    def process_con_dir(self, path):
        print "[annotations process_con_dir]path: %s" % path
        if not os.path.exists(path):
            print "Error: path %s does not exist" % path

        type = "con"
        file_type_wildcard = "*" + type
        type_path = path + type
        if not os.path.exists(type_path):
            print "Error: path %s does not exist" % type_path
            print "Make sure the directory containing this annotation type has this name"
            sys.exit()

        # loop over files in con directory
        for infile in glob.glob( os.path.join(type_path, file_type_wildcard) ):
            doc_id = utils.path2filename(infile, 0)
            #print "[process_con_dir] doc_id: %s" % doc_id
            stream = open(infile, 'r')
            # Keep a list of concepts within each doc
            self.d_docid2con_list[doc_id] = []
            for line in stream:
                new_con = Con(line, doc_id)
                doc = self.d_doc_id2doc.get(doc_id)
                # /// 1017
                #pdb.set_trace()
                # 11/17/11 PGA commented out following print.  Why was this here?
                #print "[i2b2.py loop over con dir.  doc_id: %s, file: %s, doc: %s" % (doc_id, infile, doc)
                # Because We get the error:
                # File "/home/j/anick/cnlp/lib/i2b2.py", line 935, in process_con_dir
                # doc.l_sorted_concepts.append(new_con)
                # AttributeError: 'NoneType' object has no attribute 'l_sorted_concepts'

                # This occurs when a file is "renamed" as e.g. Progress-clinical-619.txt~
                # To fix, mv Progress-clinical-619.txt~ Progress-clinical-619.txt
                
                doc.l_sorted_concepts.append(new_con)
                #print "[process_con_dir] new_con no: %i" % new_con.no
                # Ignore elements that contain an extra quotation mark
                # eg. c="severe " back pain "" 23:3 23:7||t="problem"
                if ' "' not in line:

                    self.l_con.append(new_con)
                    self.d_con_no[new_con.no] = new_con
                    self.d_con_id[new_con.con_id] = new_con
                    new_con.txt_no = self.d_docline2txt_no.get(doc_line2key(new_con.doc_id, new_con.line_start))
                    new_con.txt = self.d_docline2txt.get(doc_line2key(new_con.doc_id, new_con.line_start))
                    if not self.d_txt_no2con_list.has_key(new_con.txt_no):
                        # create an empty list to initialize this key value
                        self.d_txt_no2con_list[new_con.txt_no] = []

                    self.d_txt_no2con_list[new_con.txt_no].append(new_con)
                    self.d_docid2con_list[doc_id].append(new_con)
            stream.close()
            # sort the list of concepts with the Doc instance
            doc.sort_concepts()
    """
    * Load ast
    make ast_no (sequential)
    make ast_no => ast
    make l_ast
    make ast_id (sequentia) 
    ast_id => Ast
    con_id => Ast
    add txt_no (via con)
    """

    def process_ast_dir(self, path):
        print "[annotations process_ast_dir]path: %s" % path
        if not os.path.exists(path):
            print "Error: path %s does not exist" % path

        type = "ast"
        file_type_wildcard = "*" + type
        type_path = path + type
        if not os.path.exists(type_path):
            print "Error: path %s does not exist" % type_path
            print "Make sure the directory containing this annotation type has this name"
            sys.exit()

        for infile in glob.glob( os.path.join(type_path, file_type_wildcard) ):
            doc_id = utils.path2filename(infile, 0)
            #print "[process_ast_dir] doc_id: %s" % doc_id
            stream = open(infile, 'r')
            for line in stream:
                new_ast = Ast(line, doc_id)
                #print "[process_ast_dir] new_ast no: %i" % new_ast.no
                self.l_ast.append(new_ast)
                self.d_ast_no[new_ast.no] = new_ast
                self.d_con_id2ast[new_ast.con_id] = new_ast
                new_ast.txt_no = self.d_docline2txt_no.get(doc_line2key(new_ast.doc_id, new_ast.line_start))

            stream.close()


    """
    * Load rel
    make rel_no (sequential)
    make rel_no => rel
    make l_rel
    make c1_id, c2_id
    add c1_type, c2_type (via con_id => con)
    add c1_ast, c2_ast if type is problem (via con_id => ast)  
    """

    def process_rel_dir(self, path):
        print "[annotations process_rel_dir]path: %s" % path
        if not os.path.exists(path):
            print "Error: path %s does not exist" % path

        type = "rel"
        file_type_wildcard = "*" + type
        type_path = path + type
        if not os.path.exists(type_path):
            print "Error: path %s does not exist" % type_path
            print "Make sure the directory containing this annotation type has this name"
            sys.exit()

        for infile in glob.glob( os.path.join(type_path, file_type_wildcard) ):
            doc_id = utils.path2filename(infile, 0)
            #print "[process_rel_dir] doc_id: %s" % doc_id
            stream = open(infile, 'r')
            #pdb.set_trace()
            for line in stream:
                new_rel = Rel(line, doc_id)
                #print "[process_rel_dir] new_rel no: %i" % new_rel.no
                self.l_rel.append(new_rel)
                self.d_rel_no[new_rel.no] = new_rel
                new_rel.c1_type = self.d_con_id.get(new_rel.c1_id).type 
                new_rel.c2_type = self.d_con_id.get(new_rel.c2_id).type 
                if self.d_con_id2ast.has_key(new_rel.c1_id):
                    new_rel.c1_ast = self.d_con_id2ast.get(new_rel.c1_id).ast
                if self.d_con_id2ast.has_key(new_rel.c2_id):
                    new_rel.c2_ast = self.d_con_id2ast.get(new_rel.c2_id).ast

                new_rel.txt_no = self.d_docline2txt_no.get(doc_line2key(new_rel.doc_id, new_rel.c1_line_start))

            stream.close()



    # method on Annotations
    # Execute only for lines which have associated concepts
    def make_subtxt(self, txt_no):
        
        # fetch the txt instance
        txt = self.d_txt_no.get(txt_no)
        
        # create an empty subtxt instance
        new_subtxt = Subtxt(txt.no, txt.doc_id, txt.doc_line_no, txt.field)
        self.d_txt_no2subtxt[txt_no] = new_subtxt
        self.l_subtxt.append(new_subtxt)
        
        # Create a table of txt tokens indexed by their location in the line
        d_loc = {}
        i = 0
        for token in txt.tokens:
            d_loc[i] = token
            i += 1

        # for each concept in txt instance, modify the d_loc table values
        # such that the initial concept token location is assigned
        # a pseudotoken and subsequent token locations within the phrase are 
        # assigned ""
        # We use token_count in the name of the new subcon tokens
        token_counter = 1
        # use a temporary dictionary to remember the subcon associated with
        # each token we add into the new subtxt
        d_token2subcon = {}
        for con in self.d_txt_no2con_list.get(txt_no):
            # create a subcon to store the substitution concept info
            new_subcon = Subcon(con.no, con.con_id, con.type, token_counter, con.doc_id, con.line_start, con.head)
            # txt_no is same as txt_no
            new_subcon.txt_no = txt_no 
            self.d_subcon_no[new_subcon.no] = new_subcon
            # make sure we can retrieve it later using the con_id and con_no
            self.d_con_id2subcon[con.con_id] = new_subcon
            self.d_con_no2subcon[con.no] = new_subcon
            self.l_subcon.append(new_subcon)


            if not self.d_txt_no2subcon_list.has_key(new_subcon.txt_no):
                # create an empty list to initialize this key value
                self.d_txt_no2subcon_list[new_subcon.txt_no] = []
            self.d_txt_no2subcon_list[new_subcon.txt_no].append(new_subcon)




            # local dict...
            d_token2subcon[new_subcon.token] = new_subcon

            token_counter += 1
            # store the subcon token in the d_loc entry corresponing to the
            # location of the original concept in the original txt.
            # store a tab in the first char of the subcon token so we can recognize it later
            d_loc[con.token_start] = "\t" + new_subcon.token
            # range over all tokens in the phrase except the first
            # and set their d_loc values to null strings
            for i in range(con.token_start + 1, con.token_end + 1):
                d_loc[i] = ""
        # At this point, after creating all subcons for the subtxt, d_loc contains all the subcon tokens
        # in the first position of the original con token.  Non-con tokens remain in their places in d_loc.

        # Create the line with the substitutions
        new_subtxt.tokens = []
        new_subtxt.line = ""
        
        # new_loc is the location of the token in the new line to be created
        # In the new line, multi-word phrases are collapsed into a single token
        # so the token indexes have to be reassigned accordingly
        new_loc = 0
        #print "[make_subtxt] range: %i" % (len(txt.tokens))
        for i in range(len(txt.tokens)):
            tok = d_loc.get(i)
            if tok != "":
                # if first char of tok is tab, then handle token 
                # as substitute ("sub") token
                #print "[make_subtxt 1] tok: %s, new_loc: %i" % (tok, new_loc)
                if tok[0:1] == "\t":
                    # strip off the tab
                    tok = tok[1:]
                    #if txt.no == 7504:
                    #    pdb.set_trace()

                    # keep track of the new location for the pseudotoken
                    #print "[make_subtxt 2] tok: %s, new_loc: %i" % (tok, new_loc)
                    subcon = d_token2subcon.get(tok)
                    subcon.loc = new_loc

                # add the tok (pseudo or otherwise) to the new output list & string
                tok = tok.lstrip("\t")
                # remove the numeric identifier from tokens that have it ("__n")
                # It is better for the parser to work with real words rather than unknowns.
                suffix_start = tok.rfind("__")
                if suffix_start > -1:
                    tok = tok[0:tok.rfind("__")]
                    
                new_subtxt.tokens.append(tok)
                new_subtxt.line = new_subtxt.line + " " + tok
                new_loc += 1

        # print "[make_subtxt] line: %s\nsubtxt line: %s" % (txt.line, new_subtxt.line)

    def process_subtxt(self):
        #pdb.set_trace()
        for txt_no in self.d_txt_no2con_list.keys():
            # print "[process_subtxt] txt_no: %s" % txt_no
            self.make_subtxt(txt_no)


    # Writing out txt lines in a form for input to sdp parser
    # format is 
    # txt txt_no doc_id line_no\t<txt_line>
    def txt2sdp_input_format(self, file):
        stream = open(file, 'w')
        for txt in self.l_txt:
            line = "txt " + str(txt.no) + " " + txt.doc_id + " " + str(txt.doc_line_no) + "\t" + txt.line 
            stream.write(line + "\n")
        stream.close()

    def subtxt2sdp_input_format(self, file):
        stream = open(file, 'w')
        for subtxt in self.l_subtxt:
            line = "subtxt " + str(subtxt.no) + " " + subtxt.doc_id + " " + str(subtxt.doc_line_no) + "\t" + subtxt.line 
            stream.write(line + "\n")
        stream.close()
        
    # dump to file named "instances"
    # file parameter is full path up to extension.
    
    def dump_instance_data(self, file):
        s_con = open(file + ".con", 'w')
        s_ast = open(file + ".ast", 'w')
        s_rel = open(file + ".rel", 'w')
        s_txt = open(file + ".txt", 'w')
        s_subtxt = open(file + ".subtxt", 'w')
        s_subcon = open(file + ".subcon", 'w')

        for con in self.l_con:
            s_con.write("%s\n" % con.con2file_format())
        for ast in self.l_ast: 
            s_ast.write("%s\n" % ast.ast2file_format())
        for rel in self.l_rel:
            s_rel.write("%s\n" % rel.rel2file_format())
        for txt in self.l_txt:
            s_txt.write("%s\n" % txt.txt2file_format())
        for subtxt in self.l_subtxt:
            s_subtxt.write("%s\n" % subtxt.subtxt2file_format())
        for subcon in self.l_subcon: 
            s_subcon.write("%s\n" % subcon.subcon2file_format())

        s_con.close()
        s_ast.close()
        s_rel.close()
        s_txt.close()
        s_subtxt.close()
        s_subcon.close()

    # incremental version of dump_instance_data by type
    def dump_instance_data_type(self, file, type):
        # type is: txt con subtxt subcon ast rel 
        s_out = open(file + "." + type, 'w')

        if type == "con":
            for con in self.l_con:
                s_out.write("%s\n" % con.con2file_format())
        elif type == "ast":
            for ast in self.l_ast: 
                s_out.write("%s\n" % ast.ast2file_format())
        elif type == "rel":                
            for rel in self.l_rel:
                s_out.write("%s\n" % rel.rel2file_format())
        elif type == "txt":                
            for txt in self.l_txt:
                s_out.write("%s\n" % txt.txt2file_format())
        elif type == "subtxt":                
            for subtxt in self.l_subtxt:
                s_out.write("%s\n" % subtxt.subtxt2file_format())
        elif type == "subcon":                
            for subcon in self.l_subcon: 
                s_out.write("%s\n" % subcon.subcon2file_format())

        s_out.close()

    def pickle(self, output_file):
        s_output = open(output_file, "w")
        pickle.dump(self, s_output)
        s_output.close()



    def inspect(self, type, no, show_subtxt="0"):
        if type == "con":
            con = self.d_con_no.get(no)
            con.inspect()
            txt_no = con.txt_no
        elif type == "rel":
            rel = self.d_rel_no.get(no)
            rel.inspect()
            txt_no = rel.txt_no
        elif type == "ast":
            ast = self.d_ast_no.get(no)
            ast.inspect()
            txt_no = ast.txt_no
        pline = self.d_txt_no2pline.get(txt_no)
        pline.inspect(show_subtxt)

    ### note PGA created a version of this as an external function
    def get_lemma(self, surface, stanford_pos):
        # pdb.set_trace()
        # create the dict key from surface and stanford_pos
        first_char = stanford_pos[0]
        pos = ""
        surface = surface.lower()
        if first_char == "V":
            pos = "verb"
        elif first_char == "N":
            pos = "noun"
        # in some cases, the Stanford tagger treats a past tense verb
        # as an adjective (e.g. "noticed" => JJ)
        # To get the lemma, let's look the word up as a verb even if
        # it is tagged as JJ.  If it is not found as a verb, we'll default
        # the lemma to the surface string anyway.
        elif first_char == "J":
            pos = "verb"
        key = pos + "_" + surface
        print "[get_lemma] pos: %s, surface: %s, first_char: %s" % (pos, surface, first_char)

        if number_p(key):
            lemma = "_NUM_"
        elif self.d_lex.has_key(key):
            lemma = self.d_lex.get(key)
        # in some cases dates are coded as:
        # tag: **DATE[Oct/JJ, pos: JJ
        # tag: 2005]/CD, pos: CD

        elif surface[0:6] == "**date" or (surface[-1] == "]" and stanford_pos == "CD"):
            lemma = "_date_"

        elif stanford_pos == "CD":
            # i2b2 fails to split a period from the end of a number.
            # number and period usually signifies a list element  (1.  <something>  2. <something)
            if surface[-1] == ".":
                lemma = "_NumPeriod_"
            else:
                # CARDINAL NUMBER
                lemma = "_NUM_"
        else:
            lemma = surface
        return(lemma)

def number_p(term):
    if term in ["two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "1-2", "1-3"]:
        return(1)
    else:
        return(0)
        

    
#### Note: this should be a method of Annotations.
#### However, I needed to change it without reloading all the Annotations,
#### so I made it a function that takes annot instance as a argument
# return lemma for nouns and verbs; lowercased surface for all other pos.
# Replace numbers and dates with generic lemma
def get_lemma(annot, surface, stanford_pos):
    #  pdb.set_trace()
    # create the dict key from surface and stanford_pos
    first_char = stanford_pos[0]
    pos = ""
    surface = surface.lower()
    if first_char == "V":
        pos = "verb"
    elif first_char == "N":
        pos = "noun"
    # in some cases, the Stanford tagger treats a past tense verb
    # as an adjective (e.g. "noticed" => JJ)
    # To get the lemma, let's look the word up as a verb even if
    # it is tagged as JJ.  If it is not found as a verb, we'll default
    # the lemma to the surface string anyway.
    elif first_char == "J":
        pos = "verb"
    key = pos + "_" + surface
    # print "[get_lemma] pos: %s, surface: %s, first_char: %s" % (pos, surface, first_char)
    if annot.d_lex.has_key(key):
        lemma = annot.d_lex.get(key)
    # in some cases dates are coded as:
    # tag: **DATE[Oct/JJ, pos: JJ
    # tag: 2005]/CD, pos: CD

    elif surface[0:6] == "**date" or (surface[-1] == "]" and stanford_pos == "CD"):
        lemma = "_date_"

    elif stanford_pos == "CD":
        # i2b2 fails to split a period from the end of a number.
        # number and period usually signifies a list element  (1.  <something>  2. <something)
        if surface[-1] == ".":
            lemma = "_NumPeriod_"
        else:
            # CARDINAL NUMBER
            lemma = "_NUM_"
    else:
        lemma = surface
    return(lemma)

        

        

# pickling 

# annotations_path is directory containing annotations
# subdirectories (con, rel, ast, txt)
# output_file is full filename for pickle output
def pickle_annotations(annotations_path, output_file):
    # create annotations instance and its l_doc_id list
    # print creating annot
    annot = Annotations()
    annot.process_txt_dir(annotations_path)
    annot.process_con_dir(annotations_path)
    annot.process_ast_dir(annotations_path)
    annot.process_rel_dir(annotations_path)
    annot.process_subtxt()
    # assume lexicon is in code dir
    annot.process_lexicon("lexicon.tcl")

    """
    # save the pickled annotations data to a file
    s_output = open(output_file, 'w')
    pickle.dump(annot, s_output)
    s_output.close()
    """
    return annot



# returns the unpickled annotations instance in pickle_file
def unpickle_annotations(pickle_file):
    s_pickle = open(pickle_file, 'r')
    annot = pickle.load(s_pickle)
    s_pickle.close()
    return annot

##########################################
# parsing with SDP

#parse_subtxt(annot):


# i2b2_file is a file with one sentence per line
# txt txt_no doc_id tsent_no\tsent (where sent is whitespace separated string of tokens)
# e.g. subtxt 20 018636330_DH 57         She has no PROBLEM_1 .
# corpus_file is an output file where the pickled list of graphs is written.
# We assume the parser has been initialized as follows:
# dparser = sdpWrapper.sdpWrapper("wordsAndTags,penn,typedDependenciesCollapsed")
# Note that if the parser cannot parse an input, it writes to stderr (log.dat)
# and the subprocess hangs waiting for stdout.  SO we try to avoid this situation by
# checking the length of sentences and not sending any over max_length to the parser.
# The parser's stated max length is 100 but we can be safer by choosing a lower threshold.

# NOTE: PGA 5/17/10 For convenience, we output both readable files and a pickled file 
# containing everything within a cdb instance object here.
# sent_type is "txt" or "subtxt"
# output_dir should have final slash
# sent_file should be the input full file name 
def parse_i2b2_file(annot, sdp, output_dir, sent_type, sent_file, error_stream):
    max_length = 80

    # We read from sent_file, parse and write output to a
    # set of files.  We also add the parsed output to the annotation
    # instance and create a pickle file 
    s_sents = open(sent_file, "r")
    s_tag = open(output_dir + sent_type + ".tag", "w")
    s_penn = open(output_dir + sent_type  + ".penn", "w")
    s_tdc = open(output_dir + sent_type  + ".tdc", "w")
    s_over = open(output_dir + sent_type  + ".over", "w")
    #s_pickle = open(output_file + ".pickle", "w")

    for line in s_sents:
        line = line.strip("\n")
        (meta_data, sent) = line.split("\t")
        # create a token_list to count number of tokens, but first filter out
        # extra whitespace chars!
        sent_filtered = " ".join(sent.split())
        token_list = sent_filtered.split()
        if len(token_list) <= max_length:
            sdp.give_input(sent)
            #pdb.set_trace()
            (tags, penn, tdc)  = sdp.get_outputs()
            # The number of tokens in the original sentence should match the number in
            # the parsed output.  Check it here.
            tag_list = tags.split()
            if len(tag_list) != len(token_list):
                error_stream.write("txt len: %i, txt: %s\ntag len: %i, tags: %s\n" % (len(token_list), line, len(tag_list), tags))

            ####graph = annot.tdc2graph(tdc)

            s_tag.write("%s\t\t%s\n" % ( meta_data, tags))
            s_penn.write("%s\t\t%s\n" % ( meta_data, penn))
            s_tdc.write("%s\t\t%s\n" % ( meta_data, tdc))
        else:
            # overflow
            # set fields to empty string
            ### PGA note: If we want the part of speech tags for long sentences,
            ### we should break the sentence into pieces and call the tagger on
            ### each piece here.
            tags = ""
            penn = ""
            tdc = ""
            s_over.write("%s\n" % (line))

        # write data into Pline pred, arg_no, source_index, target_index): instance
        # If we don't have a pline for this txt_no, create one
        # This is necessary, since we load the txt and subtxt data
        # into the same pline instances but during different calls to this function.
        # The subtxt sentences can only be generated once we have received the concept data.
        meta_fields = meta_data.split()
        txt_no = int(meta_fields[1])
        doc_id = meta_fields[2]
        sent_no = int(meta_fields[3])
        #pdb.set_trace()
        if annot.d_txt_no2pline.has_key(txt_no):
            pline = annot.d_txt_no2pline.get(txt_no)
        else:
            pline = Pline(txt_no, doc_id, sent_no)
            # add pline to the dict
            annot.d_txt_no2pline[txt_no] = pline

        # populate the pline attrs based on the sent_type
        if sent_type == "txt":
            pline.txt_line = sent
            pline.txt_tag = tags
            pline.txt_penn = penn
            pline.txt_tdc = tdc
        else:
            pline.subtxt_line = sent
            pline.subtxt_tag = tags
            pline.subtxt_penn = penn
            pline.subtxt_tdc = tdc
            

    s_tag.close()
    s_penn.close()
    s_tdc.close()
    s_over.close()
    #s_pickle.close()

    """
    # pickle and output graph list
    s_corpus = open(corpus_file, 'w')
    # graph list is an ordered list of triples [doc_id. sent_no. graph]
    pickle.dump(cdb, s_corpus)
    s_corpus.close()
    """

def unpickle_plines(annot, pickle_dir):
    input_file = pickle_dir + "pline.pickle"
    if os.path.exists(input_file):
        s_input = open(input_file, "r")
        annot.d_txt_no2pline = pickle.load(s_input)
        s_input.close()




# a parsed line and its meta-data
class Pline:
    def __init__(self, txt_no, doc_id, sent_no):
        self.txt_no = txt_no
        self.doc_id = doc_id
        self.sent_no = sent_no
        self.txt_line = ""
        self.txt_tag = ""
        self.txt_penn = ""
        self.txt_tdc = ""
        self.txt_dgraph = ""
        self.subtxt_line = ""
        self.subtxt_tag = ""
        self.subtxt_penn = ""
        self.subtxt_tdc = ""
        self.subtxt_tdc_dgraph = ""

    def display(self):
        print "Pline: %i, %s, %i" % (self.txt_no, self.doc_id, self.sent_no)
        print "%s\n%s\n%s\n%s\n\n%s\n%s\n%s\n%s" % (self.txt_line, self.txt_tag, self.txt_penn, self.txt_tdc, self.subtxt_line, self.subtxt_tag, self.subtxt_penn, self.subtxt_tdc) 

    def inspect(self, show_subtxt='0'):
        print "[TXT] %s" % self.txt_line
        print "[TAG] %s" % self.txt_tag
        print "[PENN]"
        pp_penn(self.txt_penn)
        print "[TDC]" 
        pp_tdc(self.txt_tdc)
        #print "[field] %s" % self.field
        if show_subtxt == '1':
            print "[SUBTXT] %s" % self.subtxt_line
            print "[TAG] %s" % self.subtxt_tag
            print "[PENN]"
            pp_penn(self.subtxt_penn)
            print "[TDC]" 
            pp_tdc(self.subtxt_tdc)
            # should we add the field attr to pline?
            #print "[field] %s" % self.field

def pp_penn(penn):
    penn_lines = penn.split("\t")
    for penn_line in penn_lines:
        print "     %s" % penn_line

def pp_tdc(tdc):
    tdc_lines = tdc.split("\t")
    for tdc_line in tdc_lines:
        print "     %s" % tdc_line






##########################################
# data reformatting

# not currently used.
# flat lists of all rel, con, ast instances
def annot2con_list(annot):
    con_list = []
    ast_list = []
    rel_list = []
    for doc in annot.d_doc.values():
        for con in doc.l_con:
            field_list = [con.string, con.type, doc.doc_id, con.line_start, con.token_start, con.line_end, con.token_end]
            con_list.append(field_list)
        for ast in doc.l_ast:
            field_list = [ast.string, ast.type, ast.ast, doc.doc_id, ast.line_start, ast.token_start, ast.line_end, ast.token_end]
            ast_list.append(field_list)
        for rel in doc.l_rel:
            # note: we may eventually want to add the concept type values to this list
            field_list = [rel.rel, doc.doc_id, rel.c1_string, rel.c1_symbol, rel.c1_line_start, rel.c1_token_start, rel.c1_line_end, rel.c1_token_end,  rel.c2_string, rel.c2_symbol, rel.c2_line_start, rel.c2_token_start, rel.c2_line_end, rel.c2_token_end]
            rel_list.append(field_list)
            
    return([con_list, ast_list, rel_list])


def annot2con_list2file(annot, con_out, ast_out, rel_out, con_token_out, txt_token_out):
    s_con = open(con_out, 'w')
    s_ast = open(ast_out, 'w')
    s_rel = open(rel_out, 'w')
    s_txt_token = open(txt_token_out, 'w')
    s_con_token = open(con_token_out, 'w')
    for doc in annot.d_doc.values():
        for con in doc.l_con:
            s_con.write("%s\t%s\t%s\t%i\t%i\t%i\t%i\n" % (con.string, con.type, doc.doc_id, con.line_start, con.token_start, con.line_end, con.token_end))
            # output token info for computing token class probabilities
            last_token_no  = len(con.tokens) - 1
            i = 0
            # label token as b, i, e
            # e: ends a phrase
            # i: inside, neither beginning nor ending the phrase
            # b: begins a phrase longer than 1
            i = 0
            for token in con.tokens:
                lc_token = token.lower()
                if i == last_token_no:
                    token_pos = "e"
                elif i == 0:
                    # begins a phrase longer than 1 token
                    token_pos = "b"
                else:
                    token_pos = "i"
                i += 1 
                s_con_token.write("%s\t%s\t%s\t%s\t%s\n" %  (lc_token, token, con.type, token_pos, doc.doc_id))

        for ast in doc.l_ast:
            s_ast.write("%s\t%s\t%s\t%s\t%i\t%i\t%i\t%i\n" % (ast.string, ast.type, ast.ast, doc.doc_id, ast.line_start, ast.token_start, ast.line_end, ast.token_end))
        for rel in doc.l_rel:
            # note: we may eventually want to add the concept type values to this list
            s_rel.write("%s\t%s\t%s\t%s\t%i\t%i\t%i\t%i\t%i\t%i\t%i\t%i\n" % (rel.c1_string, rel.c2_string, rel.rel, doc.doc_id, rel.c1_line_start, rel.c1_token_start, rel.c1_line_end, rel.c1_token_end,  rel.c2_line_start, rel.c2_token_start, rel.c2_line_end, rel.c2_token_end))
        for txt in doc.l_txt:
            for token in txt.tokens:
                lc_token = token.lower()
                s_txt_token.write("%s\t%s\t%s\t%s\n" % (lc_token, token, txt.type, doc.doc_id))
        
    
    s_con.close()
    s_ast.close()
    s_rel.close()
    s_con_token.close()
    s_txt_token.close()

""" 
### /// in progress                            
# returns a blank separated list of features to 
def annot2rel_features(annot):
    for rel in annot.l_rel

    for doc in annot.d_doc.values():
        for con in doc.l_con:
            s_con.write("%s\t%s\t%s\t%i\t%i\t%i\t%i\n" % (con.string, con.type, doc.doc_id, con.line_start, con.token_start, con.line_end, con.token_end))
            # output token info for computing token class probabilities
            last_token_no  = len(con.tokens) - 1
            i = 0
            # label token as b, i, e
            # e: ends a phrase
            # i: inside, neither beginning nor ending the phrase
            # b: begins a phrase longer than 1
            i = 0
            for token in con.tokens:
                lc_token = token.lower()
                if i == last_token_no:
                    token_pos = "e"
                elif i == 0:
                    # begins a phrase longer than 1 token
                    token_pos = "b"
                else:
                    token_pos = "i"
                i += 1 
                s_con_token.write("%s\t%s\t%s\t%s\t%s\n" %  (lc_token, token, con.type, token_pos, doc.doc_id))

        for ast in doc.l_ast:
            s_ast.write("%s\t%s\t%s\t%s\t%i\t%i\t%i\t%i\n" % (ast.string, ast.type, ast.ast, doc.doc_id, ast.line_start, ast.token_start, ast.line_end, ast.token_end))
        for rel in doc.l_rel:
            # note: we may eventually want to add the concept type values to this list
            s_rel.write("%s\t%s\t%s\t%s\t%i\t%i\t%i\t%i\t%i\t%i\t%i\t%i\n" % (rel.c1_string, rel.c2_string, rel.rel, doc.doc_id, rel.c1_line_start, rel.c1_token_start, rel.c1_line_end, rel.c1_token_end,  rel.c2_line_start, rel.c2_token_start, rel.c2_line_end, rel.c2_token_end))
        for txt in doc.l_txt:
            for token in txt.tokens:
                lc_token = token.lower()
                s_txt_token.write("%s\t%s\t%s\t%s\n" % (lc_token, token, txt.type, doc.doc_id))
        
    
    s_con.close()
    s_ast.close()
    s_rel.close()
    s_con_token.close()
    s_txt_token.close()
                              
"""
