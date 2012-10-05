#futils.py
# generic feature operations
# 5/27/10 PGA
# 6/22/10 PGA added arff utilities
# 7/16/10 PGA added relpair utils and generation of system output directories

import pdb
import os, re, sys
import utils
import pickle
import i2b2_config
import i2b2
import utils

# debugger
import pdb

# useful predicates for pairs of concepts

def cc_same_sent_p(c1, c2):
    if c1.line_start == c2.line_start:
        return True
    else:
        return False

def cc_same_last_term_p(c1, c2):
    if c1.string.split()[-1] == c2.string.split()[-1]:
        return(1)
    else:
        return(0)
    

# the last word of both concept strings is "patient"
def cc_patient_p(c1, c2):
    if c1.string.split()[-1] == "patient" and c2.string.split()[-1] == "patient":
        return(1)
    else:
        return(0)

# one concept string is a terminal substring of the other (at a word boundary)
# e.g. futils.cc_terminal_substring_p("doctor nurse", "nurse") => 1
def cc_terminal_substring_p(c1_string, c2_string):
    len_c1 = len(c1_string)
    len_c2 = len(c2_string)

    if c1_string == c2_string:
        return(0)
    elif len_c1 < len_c2:
        start_char = len_c2 - len_c1
        end_char = len_c2
        pre_start_char = start_char - 1
        if c2_string[start_char:end_char] == c1_string and c2_string[pre_start_char] == " ":
            return(1)
        else:
            return(0)
    elif len_c2 < len_c1:
        start_char = len_c1 - len_c2
        end_char = len_c1
        pre_start_char = start_char - 1
        if c1_string[start_char:end_char] == c2_string and c1_string[pre_start_char] == " ":
            return(1)
        else:
            return(0)
    else:
        # same string length but one word, different strings
        return(0)




# inverted index from feature to annotation id (rel.no, ast.no)
class FeatIndex:
    # feat_index is created from a fully populated corpus_features instance
    def __init__(self, corpus_features):
        self.d_fi = {}

        for features in corpus_features.instance_list:
            id = features.no
            for binary_feature in features.binary_features:
                self.insert(binary_feature, id)

            for nominal_feature in features.d_nominal_features.keys():
                feature_name = nominal_feature + "=" + d_nominal_features.get(nominal_feature)
                self.insert(feature_name, id)

    # id is integer
    # feature is the feature string
    def insert(self, feature, id):
        if not self.d_fi.has_key(feature):
            self.d_fi[feature] = [id]
        else:
            self.d_fi[feature].append(id)

    def pickle(self, output):
        s_output = open(output, "w")
        pickle.dump(self, s_output)        
        s_output.close()

    def ids(self, feature):
        id_list = self.d_fi.get(feature)
        return(id_list)

def compare(fi, preds,  feature, compare_class):
    annot = preds.annot
    id_list = fi.d_fi.get(feature)
    annot_type = preds.annot_type
    class_value = ""
    # pdb.set_trace()
    for id in id_list:
        if annot_type == "rel":
            class_value = annot.d_rel_no.get(id).rel
        else:
            if annot_type == "rel":
                class_value = annot.d_ast_no.get(id).ast


        prediction = preds.d_instance_pred.get(id)
        if class_value == prediction:
            error_status = "Correct:"
        else:
            error_status = "Error:"

        if class_value == compare_class:
            print "[%i] %s Actual: %s, Predicted: %s" % (id, error_status, class_value, prediction)
            preds.inspect(id + 1)
        else:
            print "[compare]Skipping %i, class %s (%s)" % (id, class_value, error_status)
            

def unpickle_feat_index(pickle_file):
    s_pickle = open(pickle_file, 'r')
    feat_index = pickle.load(s_pickle)
    s_pickle.close()
    return feat_index

# capture features for a corpus of records for a specific annotation type
class CorpusFeatures:
    # class_values is the set of class values for this task
    def __init__(self, relation_name, cat_values):
        self.relation_name = relation_name
        # dictionary to hold counts of features
        self.d_binary_features_count = {}    
        # put values in sorted order for use in weka
        # pdb.set_trace()
        cat_values.sort()
        self.cat_values = cat_values 
        # ordered list of features instances for annotations of a single type (ast, rel, con)
        self.instance_list = []
        # list of all attrs
        self.all_attrs = []

        # create the class value list string for use in weka
        self.class_values_string = ""
        for value in self.cat_values:
            self.class_values_string = self.class_values_string + ", " + value
        # remove initial comma
        self.class_values_string = self.class_values_string[1:]


    def incr_binary_features_count(self, feat):
        if self.d_binary_features_count.has_key(feat):
            self.d_binary_features_count[feat] = self.d_binary_features_count.get(feat) + 1
        else:
            self.d_binary_features_count[feat] = 1
    
    def filter_binary_features(self, feat_list, min):
        filtered_feat_list = []
        for feat in feat_list:
            if self.d_binary_features_count.get(feat) >= min:
                filtered_feat_list.append(feat)
        return(filtered_feat_list)

    def dump_feature_counts(self, file_name):
        s_fc = open(i2b2_config.weka_dir + file_name + ".fc", "w")
        for (feat, count) in self.d_binary_features_count.items():
            s_fc.write("%i %s\n" % (count, feat))
        s_fc.close()



# instances capture features for a single record
class Features:
    # no is unique annotion id (rel.no or ast.no)
    def __init__(self, corpus_features, no):
        """
        # for training, class should have a value
        # for testing, it can be ""
        self.category = category
        # list of features provided as annotations
        # These are useful for describing input data
        # but are not used in training/testing
        self.base_features = base_features
        # list of derived features
        # to be used in training/testing
        """
        # We need corpus_features since it contains corpus wide info
        # about the frequencies of features
        self.corpus_features = corpus_features
        # value of the class, if known.  Null string if unknown.
        self.cat = ""
        self.binary_features = []
        self.d_nominal_features = {}
        # meta_data allows for storing a non-feature string with a features record
        self.meta_data = ""
        # unique identifier of the annotation record
        self.no = no

    # name and value should be strings without blanks
    # adds a feature of the form name=value to the real_features attr
    # value should be string
    def add_nominal_feature(self, name, value):
        
        # filter out duplicate features
        if not self.d_nominal_features.has_key(name):
            self.d_nominal_features[name] = value

    # name and value should be strings without blanks
    # adds a feature of the form name=value to the real_features attr
    # If value is "", then just the name is added.
    def add_binary_feature(self, name, value=""):
        if value != "":
            feature = name + "__" + value
        else:
            feature = name
        # check for blank within feature
        if feature.find(" ") > 0:
            print "[add_feature] ERROR: feature contains blank (%s, %s)" % (name, value)
        # replace any characters that might cause problems in WEKA
        feature = legalize_weka_attr(feature)
        # filter out duplicate features
        if feature not in self.binary_features:
            self.binary_features.append(feature)

        # remember to incr the count of this feature in the corpus
        self.corpus_features.incr_binary_features_count(feature)
        return(feature)

    # a way for coref<n>.py to restrict features added to a subset based
    # on the 2 char prefix of the feature name
    def add_binary_feature_pre(self, tfn, bf_prefix_list, value=""):
        if tfn[0:2] in bf_prefix_list:
            self.add_binary_feature(tfn)



    # takes a list of feature names and removes any with corpus freq < min
    def filter_binary_features(self, min):
        filtered_feats = []
        for feat in self.binary_features:
            if self.corpus_features.d_binary_features_count.get(feat) >= min:
                filtered_feats.append(feat)
        return(filtered_feats)


# features
# nth token to left
# Given a token number, find the token n items to the left

# txt, token_no, i = distance 
def nth_token_to_left(txt, token_no, i):

    index = token_no - i
    if index >= 0:
        nth_token = txt.tokens[index]
    else:
        nth_token = ""
    return nth_token

# Given a token number, find the token n items to the left
def nth_token_to_right(txt, token_no, i):
    index = token_no + i
    if index <= len(txt.tokens) - 1:
        nth_token = txt.tokens[index]
    else:
        nth_token = ""
    return nth_token

# Given a token number, find the token n items to the left
def nth_bigram_to_left(txt, token_no, i):
    index = token_no - i
    if index > 0:
        nth_bigram = txt.tokens[index - 1] + "_" + txt.tokens[index]
    else:
        nth_bigram = ""
    return nth_bigram

# Given a token number, find the token n items to the left
def nth_bigram_to_right(txt, token_no, i):
    # pdb.set_trace()
    index = token_no + i
    if index < len(txt.tokens) - 1:
        nth_bigram = txt.tokens[index] + "_" + txt.tokens[index + 1]
    else:
        nth_bigram = ""
    return nth_bigram


# path based features

# return a list of subject lemmas
def path_subj (subchart, loc):
    patterns = [ ["nsubj0"],  ["dobj1", "nsubj0"], ["prep_of1", "dobj1", "nsubj0"] ]
    path_list = []
    subjects = []

    # gather up all paths matching the pattern
    for pattern in patterns:
        pattern_paths = subchart.tdc_path_coord(loc, pattern, [], [], "f")
        for path in pattern_paths:
            path_list.append(path)
        
    # extract the subjects
    for path in path_list:
        subj = subchart.tdc_path_lemma(path, -1)
        subjects.append(subj)
        # print "[path_subj]found subject: %s" % subj
    return(subjects)

# NOTE: not implemented yet! PGA 7/26
# dobj(denies-2, fever-8)
# return a list of subject lemmas
def path_obj (subchart, loc):
    patterns = [ ["dobj"],  ["dobj1", "nsubj0"], ["prep_of1", "dobj1", "nsubj0"] ]
    path_list = []
    subjects = []

    # gather up all paths matching the pattern
    for pattern in patterns:
        pattern_paths = subchart.tdc_path_coord(loc, pattern, [], [], "f")
        for path in pattern_paths:
            path_list.append(path)
        
    # extract the objects
    for path in path_list:
        subj = subchart.tdc_path_lemma(path, -1)
        subjects.append(subj)
        # print "[path_subj]found subject: %s" % subj
    return(subjects)

                    
# term categories
def term_family_p(lemma):
    if lemma in ["family", "familial", "fam", "sister", "brother", "mother", "father", "son", "daughter", "aunt", "uncle", "grandmother", "grandfather", "niece", "nephew", "cousin", "sibling", "twin", "parent", "child", "individual", "person", "people", "someone", "somebody"]:
        return 1
    else:
        return 0

def term_negative_p(lemma):
    if lemma in ["no", "not", "non", "absent", "absence", "deny", "lack", "without", "negative", "nor", "neither", "unlikley", "reject", "rule", "eliminate", "free", "immune", "resolve", "resolved", "disappear", "fade", "go", "clear"]:
        return 1
    else:
        return 0

def term_possible_p(lemma):
    if lemma in ["may", "might", "could", "possible", "possibility", "suggest", "unsure", "question", "questionable", "consider", "postulate", "suspect", "suspicion", "apparent", "appear", "think", "thought", "feel"]:
        return 1
    else:
        return 0

def term_hypothetical_p(lemma):
    if lemma in ["if", "fear", "instructions", "detection", "avoid", "detect", "instruct", "call", "inform", "contact", "require", "report", "recommend", "recommendation", "consider"]:
        return 1
    else:
        return 0



# Note: I removed "consistent" from this list because annotators associated it with Present.
def term_probable_p(lemma):
    if lemma in ["likely", "probable", "presume", "expect"]:
        return 1
    else:
        return 0

# "your pain"
def term_definite_p(lemma):
    if lemma in ["his", "her", "your", "the", "this"]:
        return 1
    else:
        return 0

def term_absent_p(lemma):
    if lemma in ["atraumatic", "afebrile", "afeb", "atnc", "anicteric", "nohepatosplenomegaly", "unlabored", "non-tender", "nontender", "non-distended", "nondistended", "nad", "nt", "nd", "nabs", "asymptomatic", "nonproductive", "non-productive", "non-displaced", "nondisplaced", "non-dilated", "nondilated", "unlabored", "nonhypoxic", "nondysmorphic", "nkda", "nt/nd", "nt/nd/nabs", "nd/nabs", "nd/nt", "nabs/nt", "nabs/nd"]:
        return 1
    else:
        return 0


def term_worsen_p(lemma):
    if lemma in ["exacerbate", "exacerbated", "rupture", "droop", "trigger", "avoid", "burn", "obstruct", "occlude", "occluding"]:
        return 1
    else:
        return 0

def term_improve_p(lemma):
    if lemma in ["improve", "ameliolate", "help", "correct", "subside", "disappear", "clear", "resolve"]:
        return 1
    else:
        return 0

def term_need_p(lemma):
    if lemma in ["require", "necessitate", "need", "warrant"]:
        return 1
    else:
        return 0


def term_treat_p(lemma):
    if lemma in ["administer", "give", "apply", "attempt", "begin", "dispense", "start", "perform"]:
        return 1
    else:
        return 0

def term_apply_treatment_p(lemma):
    if term_treat_p(lemma) or term_need_p(lemma) or term_improve_p(lemma) or term_worsen_p(lemma):
        return 1
    else:
        return 0
    
def term_test_p(lemma):
    if lemma in ["show", "demonstrate", "indicate", "suggest", "confirm", "affirm", "reaffirm", "reveal", "measure", "be"," respond", "assess", "retest", "retested", "test", "examine", "investigate", "evaluation", "evaluate"]:
        return 1
    else:
        return 0

def term_stop_p(lemma):
    if lemma in ["withdraw", "stop", "terminate", "finish", "end"]:
        return 1
    else:
        return 0

def ng_possible_p(ngram):
    if ngram in ["perhaps", "not_exclude", "vs", "versus", "evidence", "appear_to_be", "think_to", "suggest", "consistent_with", "indicate", "think_to", "suggestive", "may_have", "study_of", "compatible_with" ]:
        return 1
    else:
        return 0


# load the semantic category dictionary used in ngram production
def load_semcat():
    d_semcat = {}
    s_semcat = open(i2b2_config.lexicon_dir + "semcat.txt", "r")
    # file format is SEMCAT_TAG\tlemma,lemma....
    for line in s_semcat:
        # comment out semcat lines with #
        if line[0] != "#":
            line = line.strip()
            line_parts = line.split("\t")
            semcat = line_parts[0]
            lemmas = line_parts[1].split(",")
            for lemma in lemmas:
                # assume each term only appears in one semcat for now
                d_semcat[lemma] = semcat
    s_semcat.close()
    sys.stderr.write("semcat dictionary loaded\n")
    return d_semcat


# load the feature generalization rules
# These map a feature name to a more general feature
def load_fgen():
    d_fgen = {}
    s_fgen = open(i2b2_config.lexicon_dir + "fgen.txt", "r")
    # file format is general_feature\tfeature feature....
    for line in s_fgen:
        # comment out fgen lines with #
        if line[0] != "#":
            line = line.strip()
            line_parts = line.split("\t")
            fgen = line_parts[0]
            features = line_parts[1].split(" ")
            for feature in features:
                # a feature could generalize into more than one fgen, so the
                # value of each dictionary entry is a list of fgens
                feature = feature.lower()
                if d_fgen.has_key(feature):
                    d_fgen[feature].append(fgen)
                else:
                    d_fgen[feature] = [fgen]
    s_fgen.close()
    sys.stderr.write("fgen dictionary loaded\n")
    return d_fgen


# load the semantic category dictionary used in ngram production
def load_noise():
    d_noise = {}
    s_noise = open(i2b2_config.lexicon_dir + "noisewords.txt", "r")
    # file format is one word per line
    for line in s_noise:
        line = line.strip()
        d_noise[line] = 1
    s_noise.close()
    sys.stderr.write("noiseword dictionary loaded\n")
    return d_noise


# return a dict of medical affixes
def load_affixes():
    d_affixes = {}
    s_affixes = open(i2b2_config.lexicon_dir + "affixes.txt", "r")
    for line in s_affixes:
        line = line.strip().lower()
        if line != "":
            d_affixes[line] = 1
        
    s_affixes.close()
    return(d_affixes)

def legalize_weka_attr(feature):
    #if feature.find('%') > 0:
    #    pdb.set_trace()
    # replace certain chars that might cause problems in weka
    # " \ ' ,
    f = feature.replace('"', '_Q_')
    f = f.replace("'", "_A_")
    f = f.replace("\\", "_B_")
    f = f.replace(",", "_C_")
    f = f.replace('%', "_P_")
    f = f.replace('{', "_OB_")
    f = f.replace('}', "_CB_")
    return(f)

# output a string in the .rel file format for the concept
# e.g. c="sign of infection" 25:21 25:23|
def concept_rel_formatted_string(con):
    cps = "c=\"" + con.string + "\" " + str(con.line_start) + ":" + str(con.token_start) + " " + str(con.line_start) + ":" + str(con.token_end)
    return(cps)

class RelPairAnnotations:
    def __init__(self, annot):
        # map from relpair number to relpair
        self.d_relpair_no = {}
        # map from c1_c2 key to rel_no
        self.d_ckey2rel_no = {}
        # list of c1_c2 and c2_c1 numbers for pairs of concepts that
        # are present in rel annotation input
        self.l_present_pair = []
        self.relpair_list = []

        
        # populate list of relpairs and d_relpair_no dict
        self.create_rel_pairs(annot)

    # 1/18/11 PGA
    # Because the i2b2 data does not include explicit records for the norel cases,
    # we need to add them to the annot rel data.  We do that here.
    def update_annot_rels(self, annot):
        i2b2.Rel.next_no = len(annot.l_rel)
        print "[update_annot_rels]Rel.next_no reset to %i" % i2b2.Rel.next_no
        self.label_relpairs_make_rels(annot)
        return(annot)

    def pickle(self):
        output_file = i2b2_config.pickle_dir + "annot_rp.pickle"
        s_output = open(output_file, "w")
        pickle.dump(self, s_output)
        s_output.close()

    # Create potential rel records from con occurrences within the same sentence
    def create_rel_pairs(self, annot):
        # problem concepts found in sentence
        problem_list = []
        # non-problem concepts found in sentence
        other_list = []
        con_list = []
        # pairs of concepts comprising potential relations
        self.relpair_list = []
        # we need an ordered list for each rp type to use when debugging weka errors
        self.l_rp_treatment = []
        self.l_rp_test = []
        self.l_rp_problem = []

        relpair_no = 0
        
        for txt in annot.l_txt:
            # initialize lists for each sentence
            problem_list = []
            other_list = []
            # if the txt line contains concept(s)
            if annot.d_txt_no2con_list.has_key(txt.no):
                con_list = annot.d_txt_no2con_list.get(txt.no)
                if len(con_list) > 1:
                    # we have multiple concepts in the sentence
                    # Divide them into problem and other
                    for con in con_list:
                        if con.type == "problem":
                            problem_list.append(con)
                        else:
                            other_list.append(con)
                # create relation pairs
                # First handle problems and others
                seen_problem_list = []
                for problem in problem_list:
                    seen_problem_list.append(problem.no)
                    for other in other_list:
                        new_rp = RelPair( relpair_no, txt.doc_id, other, problem)
                        self.relpair_list.append(new_rp)
                        self.d_relpair_no[relpair_no] = new_rp
                        relpair_no += 1
                        if other.type == "treatment":
                            self.l_rp_treatment.append(new_rp)
                        elif other.type == "test":
                            self.l_rp_test.append(new_rp)
                                
                    for p2 in problem_list:
                        if p2.no not in seen_problem_list:
                            new_rp = RelPair( relpair_no, txt.doc_id, problem, p2)
                            self.relpair_list.append(new_rp)
                            relpair_no += 1
                            self.l_rp_problem.append(new_rp)

    # using the actual rel data, label the potential relpairs as
    # present or absent
    def label_relpairs(self, annot):
        present_count = 0
        absent_count = 0
        present_pair_list = []
        rel_count = 0
        for rel in annot.l_rel:
            rel_count += 1
            # create list of c1_c2 ids
            # we can't go directly from con_id to con_no, so we have to fetch the con
            c1_no = annot.d_con_id.get(rel.c1_id).no
            c2_no = annot.d_con_id.get(rel.c2_id).no
            # store keys in both orders since we don't know which one i2b2 used for any
            # particular pair
            ckey1 = str(c1_no) + "_" + str(c2_no)
            ckey2 = str(c2_no) + "_" + str(c1_no)
            present_pair_list.append(ckey1)
            present_pair_list.append(ckey2)

            # Store the rel.no for each concept pair key
            if self.d_ckey2rel_no.has_key(ckey1):
                print "Rel: %i repeated, with key: %s" % (rel.no, ckey1)
            if self.d_ckey2rel_no.has_key(ckey2):
                print "Rel: %i repeated, with key: %s" % (rel.no, ckey2)

            self.d_ckey2rel_no[ckey1] = rel.no
            self.d_ckey2rel_no[ckey2] = rel.no

        
            
        # Now test the potential rel pairs to see if their concept pairs appear in the present list.
        for relpair in self.relpair_list:
            key = str(relpair.c1.no) + "_" + str(relpair.c2.no)
            #print "[label_relpairs] %s:" % (key),
            if key in present_pair_list:
                status = "present"
                relpair.rel = "1"
                present_count += 1
                # "0" is already set by default, so we don't need to set it here.
            else:
                status = "absent"
                absent_count += 1
            #print "%s" % status
        print "total: %i, present: %i, absent: %i, p+a: %i, Number Rel instances: %i" % (len(self.relpair_list), present_count, absent_count, present_count + absent_count, rel_count)
        # print counts of each rp type
        print "Number of type [problem, test, treament]: %i, %i, %s" % (len(self.l_rp_problem), len(self.l_rp_test), len(self.l_rp_treatment))
        
        # write out the pickled annot_rp file
        self.pickle()
        print "[label_relpairs] Created %s" % (i2b2_config.pickle_dir + "annot_rp.pickle")

    # For unknown relpairs, set their rel value to "?"
    def label_relpairs_unkn(self):
        rp_count = 0
        for relpair in self.relpair_list:
                relpair.rel = "?"
                rp_count += 1
        print "[label_repairs_unkn] total rp instances: %i" % rp_count
        
        # write out the pickled annot_rp file
        self.pickle()
        print "[label_relpairs_unkn] Created %s" % (i2b2_config.pickle_dir + "annot_rp.pickle")



    # 1/18/11 PGA
    # using the actual rel gold data, determine which pairs are new, label them
    # and create rel instances for them
    def label_relpairs_make_rels(self, annot):
        present_count = 0
        absent_count = 0
        present_pair_list = []
        rel_count = 0
        for rel in annot.l_rel:
            rel_count += 1
            # create list of c1_c2 ids
            # we can't go directly from con_id to con_no, so we have to fetch the con
            c1_no = annot.d_con_id.get(rel.c1_id).no
            c2_no = annot.d_con_id.get(rel.c2_id).no
            # store keys in both orders since we don't know which one i2b2 used for any
            # particular pair
            ckey1 = str(c1_no) + "_" + str(c2_no)
            ckey2 = str(c2_no) + "_" + str(c1_no)
            present_pair_list.append(ckey1)
            present_pair_list.append(ckey2)

            # Store the rel.no for each concept pair key
            if self.d_ckey2rel_no.has_key(ckey1):
                print "Rel: %i repeated, with key: %s" % (rel.no, ckey1)
            if self.d_ckey2rel_no.has_key(ckey2):
                print "Rel: %i repeated, with key: %s" % (rel.no, ckey2)

            self.d_ckey2rel_no[ckey1] = rel.no
            self.d_ckey2rel_no[ckey2] = rel.no
            
        # Now test the potential rel pairs to see if their concept pairs appear in the present list.
        for relpair in self.relpair_list:
            key = str(relpair.c1.no) + "_" + str(relpair.c2.no)
            #print "[label_relpairs] %s:" % (key),
            if key in present_pair_list:
                status = "present"
                relpair.rel = "1"
                present_count += 1
                # "0" is already set by default, so we don't need to set it here.
            else:
                status = "absent"
                absent_count += 1
                # create a rel for this relpair
                # To do so, we will need to create a string that looks like the rel data
                # as formatted in the .rel data file
                # Note that because of the way we created relpair instances, the 2nd concept will always
                # be of type problem.  So we can safely construct the rel line using relpair.c1 as the first concept
                
                if relpair.c1.type == "problem":
                    c1_abbrev = "P"
                elif relpair.c1.type == "treatment":
                    c1_abbrev = "Tr"
                elif relpair.c1.type == "test":
                    c1_abbrev = "Te"

                if relpair.c2.type == "problem":
                    c2_abbrev = "P"
                elif relpair.c2.type == "treatment":
                    c2_abbrev = "Tr"
                elif relpair.c2.type == "test":
                    c2_abbrev = "Te"

                norel_string = "\"" + "None" + c1_abbrev + c2_abbrev + "\""
                rel_line = concept_rel_formatted_string(relpair.c1) + "||r=" + norel_string + "||" + concept_rel_formatted_string(relpair.c2)
                #pdb.set_trace()
                new_rel = i2b2.Rel(rel_line, relpair.doc_id)
                print "new_rel_no: %i, doc_id: %s, rel_line: %s" % (new_rel.no, relpair.doc_id, rel_line)
                #///

                annot.l_rel.append(new_rel)
                annot.d_rel_no[new_rel.no] = new_rel
                new_rel.c1_type = annot.d_con_id.get(new_rel.c1_id).type 
                new_rel.c2_type = annot.d_con_id.get(new_rel.c2_id).type 
                if annot.d_con_id2ast.has_key(new_rel.c1_id):
                    new_rel.c1_ast = annot.d_con_id2ast.get(new_rel.c1_id).ast
                if annot.d_con_id2ast.has_key(new_rel.c2_id):
                    new_rel.c2_ast = annot.d_con_id2ast.get(new_rel.c2_id).ast

                new_rel.txt_no = annot.d_docline2txt_no.get(i2b2.doc_line2key(new_rel.doc_id, new_rel.c1_line_start))

            #print "%s" % status
        print "total: %i, present: %i, absent: %i, p+a: %i, Number Rel instances: %i" % (len(self.relpair_list), present_count, absent_count, present_count + absent_count, rel_count)
        # print counts of each rp type
        print "Number of type [problem, test, treament]: %i, %i, %s" % (len(self.l_rp_problem), len(self.l_rp_test), len(self.l_rp_treatment))
        
        # write out the pickled annot file
        annot.pickle(i2b2_config.pickle_dir + "annot_rel_norel.pickle")
        print "[label_relpairs] Created %s" % (i2b2_config.pickle_dir + "annot_rel_norel.pickle")
        
    # For unknown relpairs, set their rel value to "?"
    def label_relpairs_unkn(self):
        rp_count = 0
        for relpair in self.relpair_list:
                relpair.rel = "?"
                rp_count += 1
        print "[label_repairs_unkn] total rp instances: %i" % rp_count
        
        # write out the pickled annot_rp file
        self.pickle()
        print "[label_relpairs_unkn] Created %s" % (i2b2_config.pickle_dir + "annot_rp.pickle")


class RelPair:
    def __init__(self, relpair_no, doc_id, c1, c2):
        self.no = relpair_no
        self.doc_id = doc_id
        self.c1 = c1
        self.c2 = c2
        # rel = 1 if this pair of concepts is present in the rel annotation data
        # "0" otherwise
        # This is the class attribute for weka
        self.rel = "0"
        # type is problem, treatment, test
        # c1 determines the type
        self.type = c1.type

        # duplicate a bunch of rel fields that we need for rp.py
        # (which shares code with rel.py)
        self.txt_no = c1.txt_no
        self.c1_token_start = c1.token_start
        self.c1_token_end = c1.token_end
        self.c2_token_start = c2.token_start
        self.c2_token_end = c2.token_end
        self.c1_type = c1.type
        self.c2_type = c2.type
        self.c1_id = c1.con_id
        self.c2_id = c2.con_id

    def inspect(self, stream = ""):
        if stream == "":
            print "[RP] %s (%s: %s |%s: %s) (txt %i)" % (self.rel, self.c1_type, self.c1.string, self.c2_type, self.c2.string, self.txt_no)
        else:
            stream.write("[RP] %s (%s: %s |%s: %s) (txt %i)" % (self.rel, self.c1_type, self.c1.string, self.c2_type, self.c2.string, self.txt_no))


    def i2b2_format_unknown(self):
        c1_prefix = ""
        c2_prefix = ""
        c1 = self.c1
        c2 = self.c2
        
        if c1.type == "problem":
            c1_prefix = "P"
        elif c1.type == "treatment":
            c1_prefix = "Tr"
        else:
            c1_prefix = "Te"

        if c2.type == "problem":
            c2_prefix = "P"
        elif c1.type == "treatment":
            c2_prefix = "Tr"
        else:
            c2_prefix = "Te"

        # The ^ around the Rel type string are there to make it easy to substitute predictions later, if needed
        # rel_record = "c=\"" + c1.string + "\" " + str(c1.line_start) + ":" + str(c1.token_start) + " " + str(c1.line_end) + ":" + str(c1.token_end) + "||\"^" + c1_prefix + "_" + c2_prefix + "^\"||c=\""  + c2.string + "\" " + str(c2.line_start) + ":" + str(c2.token_start) + " " + str(c2.line_end) + ":" + str(c2.token_end)
        
        # NOTE: PGA replaced the relation with "?" to satisfy the needs of the weka arff file
        # (? is value for unknown class)
        rel_record = "c=\"" + c1.string + "\" " + str(c1.line_start) + ":" + str(c1.token_start) + " " + str(c1.line_end) + ":" + str(c1.token_end) + "||r=\"?\"||c=\""  + c2.string + "\" " + str(c2.line_start) + ":" + str(c2.token_start) + " " + str(c2.line_end) + ":" + str(c2.token_end)

        return(rel_record)

def unpickle_annot_rp():
    s_pickle = open(i2b2_config.pickle_dir + "annot_rp.pickle", 'r')
    annot_rp = pickle.load(s_pickle)
    s_pickle.close()
    return annot_rp

# unpickle the annot created by rpa.label_relpairs_make_rels(a)
def unpickle_annot_rel_norel():
    s_pickle = open(i2b2_config.pickle_dir + "annot_rel_norel.pickle", 'r')
    annot_rel_norel = pickle.load(s_pickle)
    s_pickle.close()
    return annot_rel_norel


# weka output is suitable for input to weka as sparse vectors
# feat_output is a list of all features, suitable for sort | uniq -c

# i2b2.weka_ast_features(i, "/Users/panick/peter/my_documents/brandeis/i2b2/v3/weka/ast.weka", "/Users/panick/peter/my_documents/brandeis/i2b2/v3/weka/ast.feats")

# min is a minimum threshold for binary feature occrrences.  Features that appear fewer than min times overall
# are not output.
# filter_arff is the path to an arff file that we wish to use to
# filter attributes when constucting a test arff file.  e.g., if we
# used weka attribute selection (chi2) to rank and filter attrs to create
# the arff used to construct a model, we'll need to use the same attrs when
# building a new test set to run through the model.  

def weka_features(corpus_features, min, weka_output, feat_output, filter_arff = ""):
    
    s_weka_output = open(weka_output, 'w')
    s_feat_output = open(feat_output, 'w')
    d_attr_index = {}
    ordered_attr_list = []
    all_attrs = corpus_features.all_attrs
    # print "[weka] all_attrs: %s" % all_attrs
    instance_list = corpus_features.instance_list

    relation_name = corpus_features.relation_name
    class_values_string = corpus_features.class_values_string

    # NOTE: This is where we create list of features f 

    # now we have the global attr info and all instances
    # write them out in weka format

    s_weka_output.write( "@RELATION %s\n\n" % relation_name )

    # for debugging, compare corpus filtered and unfiltered features lists
    # pdb.set_trace()

    # /// here is where we assign numbers to attributes.  If already have a mapping (e.g. from
    # applying weka chi2 attribute ranking to a previous set of attrs), apply it here.

    # if filter_arff exists, then read the file and construct a dictionary
    # mapping each attribute to its ordinal position (d_attr_index)

    if filter_arff != "":
        s_filter_arff = open(filter_arff, "r")
        print "[weka_features] Building attr list based on file: %s" % filter_arff
        attr_no = 0
        for line in s_filter_arff:
            if line[0:5].lower() == "@attr":
                # line defines an attr
                fields = line.split()
                attr_name = fields[1]
                ordered_attr_list.append(attr_name)
                d_attr_index[attr_name] = attr_no
                attr_no += 1

        s_filter_arff.close()

        for attr in ordered_attr_list:
            if attr == "class":
                # class should be the last attr
                s_weka_output.write( "@ATTRIBUTE class {" + class_values_string + "}\n")
            else:
                # write out attr as nominal attr with two values (0, 1)
                s_weka_output.write( "@ATTRIBUTE %s {0, 1}\n" % attr)

    else:

        print "[weka_features] Building attrs based on corpus features"
        # In the case where we are not using a set of attrs from an existing arff file,
        # we now have all the attrs defined but need to create the mapping from
        # attr string to numberic index for weka.  We need to create this mapping only
        # for the attrs we will actually keep - those with freq >= min.
        # We start numbering with index 0 (to be consistent with weka numbering
        # and make the class attr the last one.  This way we do not have to change the
        # mapping when we do tests that are missing the class attr.
        next_all_attrs_index = 0

        for attr in corpus_features.filter_binary_features(all_attrs, min):
            d_attr_index[attr] = next_all_attrs_index
            next_all_attrs_index += 1

        # now add the mapping for the class attr
        d_attr_index["class"] = next_all_attrs_index

        for attr in corpus_features.filter_binary_features(all_attrs, min):
            s_weka_output.write( "@ATTRIBUTE %s {0, 1}\n" % attr)

        # make class the last attr
        s_weka_output.write( "@ATTRIBUTE class {" + class_values_string + "}\n")

        # /// end section to generate ordered, filtered attr list for weka arff file.
    
    s_weka_output.write( "\n@DATA\n" )

    # process each instance feature set
    for features in instance_list:

        # initialize a string in which to place the sparse feature representation
        sparse_string_data = ""

        # Get the value (cat) of the class attr
        cat = features.cat
        # print "[weka class value] cat: %s" % cat

        # strip any final " on the cat, resulting from earlier bug in parsing ast record
        cat = cat.strip('"')
        
        # We need to translate each attr into its corresponding numeric index and then sort them,
        # since weka requires them to be written out in sorted order in the spare data arff format.
        weka_features = []

        # for debugging, compare filtered and unfiltered features lists
        # pdb.set_trace()

        for feat in features.filter_binary_features(min):
            # Only include attrs that also appear in d_attr_index, since in the case of
            # using a filter_arff, not all features are guaranteed to be in d_attr_index.
            if d_attr_index.has_key(feat):
                weka_features.append(d_attr_index.get(feat))
                # write out the feature in its human readable form, one per line
                # We use this file to sort | uniq and count the features
                s_feat_output.write("%s\n" % feat)
        
        # sort in place
        weka_features.sort()

        for feat in weka_features:
            feat = str(feat)
            sparse_string_data = sparse_string_data + ", " +  feat + " 1"

        # add in the class feature and value last
        sparse_string_data = sparse_string_data + ", " + str(d_attr_index.get("class")) + " " + cat
        # print "[weka] adding cat: %s" % cat

        # use slice [1:] to remove the initial comma from sparse_string_data
        
        sparse_string = "{ " + sparse_string_data[1:] + " }"
        s_weka_output.write("%s\n" % sparse_string ) 
        # For debugging, show the actual feature names, ast and txt no
        #print "%i, %s, %s" % (ast.no, ast.txt_no, debug_string)

    s_weka_output.close()
    s_feat_output.close()

# PGA 1/6/11
# mallet_features
# Creates a mallet text file for maxent classification
# filter_attrs is a file containing a list of attrs to be retained.  If "", retain all.
# assume one attr per line
# If meta_data string is non-empty, it is appended to line output after "|||"
# Use meta_data for non-feature info such as concept and text line
# output format is:
# <category label>|||<feature feature ...>|||<metadata>
def mallet_features(corpus_features, min, mallet_output, filter_attrs):
    print "[futils.py mallet_features] Preparing to output feature instances to %s." % mallet_output
    s_mallet_output = open(mallet_output, 'w')
    d_attr_index = {}
    ordered_attr_list = []
    all_attrs = corpus_features.all_attrs
    # print "[mallet] all_attrs: %s" % all_attrs
    instance_list = corpus_features.instance_list

    relation_name = corpus_features.relation_name
    class_values_string = corpus_features.class_values_string

    # NOTE: This is where we create list of features f 

    # now we have the global attr info and all instances
    # write them out in mallet format

    # for debugging, compare corpus filtered and unfiltered features lists
    #pdb.set_trace()

    # /// here is where we assign numbers to attributes.  If already have a mapping (e.g. from
    # applying weka chi2 attribute ranking to a previous set of attrs), apply it here.

    # if filter_attrs exists, then read the file and construct a dictionary
    # mapping each attribute to its ordinal position (d_attr_index)
    # leave this functionality out for now.  We may want to filter by # attrs or score

    # process each instance feature set
    feat_id = 0
    for features in instance_list:

        # initialize a string in which to place the sparse feature representation
        sparse_string_data = ""

        # Get the value (category label) of the class attr
        cat = features.cat
        # print "[mallet class value] cat: %s" % cat

        # First thing on the line will be the identifier (feat_id)
        # 7/1/11 PGA removing the feat_id from the output
        # since it seems to be interfering with the scripts for extracting predictions
        # from mallet output (pred_feats.sh)
        # sparse_string_data = str(feat_id)

        # strip any final " on the cat, resulting from earlier bug in parsing ast record
        cat = cat.strip('"')
        sparse_string_data = cat

        # track whether any features were actually output.  If not, we will have to add
        # an empty feature field (i.e. a whitespace separator) for mallet output format to be correct.
        feat_found_p = 0
        #pdb.set_trace()
        for feat in features.filter_binary_features(min):
            # Only include attrs that also appear in d_attr_index, since in the case of
            # Add feature filtering here later
            # if d_attr_index.has_key(feat):

            feat = str(feat)
            sparse_string_data = sparse_string_data + " " + feat 
            feat_found_p = 1
            
        #pdb.set_trace()
        # If there is meta_data, add it at the end after " |"
        sparse_string_data = sparse_string_data + " |"
        if features.meta_data != "":
            sparse_string_data = sparse_string_data + features.meta_data
        s_mallet_output.write("%s\n" % sparse_string_data ) 
        # For debugging, show the actual feature names, ast and txt no
        #print "%i, %s, %s" % (ast.no, ast.txt_no, debug_string)

        feat_id = feat_id + 1
        
    s_mallet_output.close()


        
# test the length of original txt and sdp parse output
def test_sdp_len(annot):
    count = 0
    errcount = 0
    for pline in annot.d_txt_no2pline.values():
        count += 1
        len_txt_line = len(pline.txt_line.strip(" ").split())
        len_txt_tag = len(pline.txt_tag.strip(" ").split())

        if len_txt_line != len_txt_tag:
            print("txt len: %i, txt: %s\ntag len: %i, tags: %s\n" % (len_txt_line, pline.txt_line, len_txt_tag, pline.txt_tag))
            errcount += 1
    print "count: %i, errcount: %i" % (count, errcount)

# sentence feature data structure

class ChartColumn:
    
    def __init__(self, column_no, token):
        self.token = token
        self.col_no = column_no
        # we'll replace the lemma later with the actual lemma string
        self.lemma = token.lower()
        self.pos = ""
        # list of chartdep instances representing doms and mods of the current word
        self.tdc_deps = []
        self.con_type = ""
        self.con_no = -1
        self.con_start = -1
        self.con_end = -1
        self.next_con_start = -1
        self.prev_con_end = -1
        self.next_same_type_con_start = -1
        self.prev_same_type_con_end = -1
        # semantic category
        # currently a single category, this may eventually be turned into a list valued attr.
        # semcat discontinued after rel_12, reinstated at rel_16
        self.semcat = ""
        
    def display(self):
        #pdb.set_trace()
        print "token: %s\ncol_no: %i\nlemma: %s\npos: %s\ncon_type: %s\ncon_no: %i\ncon_start: %i\ncon_end: %i\nnext_con_start: %i\nprev_con_end: %i\nnext_same_type_con_start: %i\nprev_same_type_con_end: %i\n" % (self.token, self.col_no, self.lemma, self.pos, self.con_type, self.con_no, self.con_start, self.con_end, self.next_con_start, self.prev_con_end, self.next_same_type_con_start, self.prev_same_type_con_end)
        for dep in self.tdc_deps:
            dep.display()




# dep representation on the chart as a pred connecting two chart columns
# arg_no (0 or 1) indicates which dependency arg this column's term is.
# pred is the tdc pred with 0 or 1 appended, indicating whether the source column is
# the 0 or 1 arg of the dependency.  The 0 arg is the dominant one, 1 the modifier.
# source and target indexes are the chart indexes of the two args. dep is the dependency in
# the format output by sdp.
# 
class ChartDep:
    def __init__(self, pred, arg_no, source_index, target_index, dep):
        self.pred = pred
        self.arg_no = arg_no
        self.source_index = source_index
        self.target_index = target_index
        self.dep = dep

    def display(self):
        print "dep: %s, pred: %s, target: %i" % (self.dep, self.pred, self.target_index)

# take a dependency as output by sdp and returns predicate and args and arg locations as a list.
# To change arg locations to be 0 based, set base = 0 (default)
def parse_dep(dep, base = 0):
    # print "[parse_dep] dep: %s" % dep
    # input is of the form, e.g.
    # dobj(had-21, aspiration-24)
    pred = dep[0:dep.find("(")]
    # remove both parens from the args section
    arg_section = dep[dep.find("(") + 1:len(dep) - 1]
    #pdb.set_trace()
    (arg0, arg1) = arg_section.split(", ")
    arg0_num = int(arg0[arg0.rfind("-") + 1:])
    arg1_num = int(arg1[arg1.rfind("-") + 1:])
    arg0_token = arg0[0:arg0.find("-") - 1]
    arg1_token = arg1[0:arg1.find("-") - 1]

    pred0 = pred + "0"
    pred1 = pred + "1"
    if base == 0:
        arg0_num = arg0_num -1
        arg1_num = arg1_num -1
    return([pred, pred0, pred1, arg0_token, arg0_num, arg1_token, arg1_num])

# structure for accessing sentence features by token number (0 based)
# We need to pass in an annotations instance since it contains the info about concepts and
# subconcepts within a txt (or subtxt)
# sub_p = 1 if sent is a subtxt, 0 if a txt instance

class Chart:

    def __init__(self, annot, txt_no, sub_p = 0):
        # get the pline for the given txt_no
        self.txt_no = txt_no
        pline = annot.d_txt_no2pline.get(txt_no)

        if pline == None:
            pdb.set_trace()
            #print "Chart: pline value is None"
        if sub_p == 0:
            
            self.sent = pline.txt_line.strip(" ")
            self.tag = pline.txt_tag.strip(" ")
            self.penn = pline.txt_penn.strip(" ")
            self.tdc = pline.txt_tdc.strip(" ")
        else:
            # create a chart for the sub(stitute) concepts
            self.sent = pline.subtxt_line.strip(" ")
            self.tag = pline.subtxt_tag.strip(" ")
            self.penn = pline.subtxt_penn.strip(" ")
            self.tdc = pline.subtxt_tdc.strip(" ")


        # print "[chart init]sent: %s" % self.sent
            
        # mapper from con_no to chart index
        self.d_con_no2index = {}

        # generate a list of columns
        self.col = []
        column_no = 0

        ###
        # tlist = self.sent.split()
        # print "number of tokens in sent: %i" % len(tlist)
        # print "tlist: %s" % tlist
        for token in self.sent.split():
            new_col = ChartColumn(column_no, token)
            column_no += 1
            self.col.append(new_col)
            ###
            #print "added col: %i" % column_no
        self.length = column_no 
        self.max = column_no - 1

        # add the part of speech to each column
        index = 0
        for tag in self.tag.split():
            self.col[index].pos = tag[tag.rfind("/") + 1:]
            token = tag[0:tag.rfind("/")]
            # print "[chart init]tag: %s, pos: %s" % (tag, self.col[index].pos)
            # self.col[index].lemma = annot.get_lemma(token, self.col[index].pos)
            # using the external version of get_lemma for now
            lemma = i2b2.get_lemma(annot, token, self.col[index].pos)
            self.col[index].lemma = lemma
            if d_semcat.has_key(lemma):
                self.col[index].semcat = d_semcat.get(lemma)

            index += 1


        # add dependency relations to the chart using both source and target indices.
        # the predicate will be named as the concatenation of relation and arg_no.
        # sdp token indices(e.g. dobj(had-21, aspiration-24))  have to be modified to be 0 based for consistency
        # with i2b2 labels.  sdp indices are 1 based.

        # test that there are actually some deps in the output, since
        # some lines might not produce any.
        if self.tdc != "":
            # print "tdc: %s" % self.tdc
            for dep in self.tdc.split("\t"):
                #pdb.set_trace()
                # ///NOTE:  Stanford deps use the nomenclature <num>' to handle certain cases of
                # conjuncts.  eg. for the sentence
                # a CT scan of the head with and without contrast was performed
                # we get two deps for head:
                # parse_dep] dep: prep_of(scan-6, head-9)
                # [parse_dep] dep: prep_of(scan-6, head-9')
                # for the cases of "with" and "without"
                # For now, we cannot handle these primed locations on the chart, so
                # we filter any deps containing a prime out here.
                if dep.find("'") < 0:

                    (pred, pred0, pred1, arg0_token, arg0_num, arg1_token, arg1_num) = parse_dep(dep, 0)
                    # now load the info into the chart
                    # pdb.set_trace()
                    col0 = self.col[arg0_num]
                    col1 = self.col[arg1_num]
                    col0.tdc_deps.append(ChartDep( pred0, 0, arg0_num, arg1_num, dep ))
                    col1.tdc_deps.append(ChartDep( pred1, 1, arg1_num, arg0_num, dep ))
            
        # to get the locations of concepts in the line
        # use annot.d_txt_no2con_list
        if annot.d_txt_no2con_list.has_key(txt_no):
            con_list = annot.d_txt_no2con_list.get(txt_no)
            #pdb.set_trace()
            l_con_info = []
            #l_subcon_info = []    # used if sub_p == 1
            # note that if sub_p == 1, we will create a subcon list based on this
            # con_list below.  For now, we just make the con_list.
            for con in con_list:
                start = con.token_start
                end = con.token_end
                type = con.type
                no = con.no
                l_con_info.append([start, end, type, no])
            # sort the l_con_info by start location
            # descending sort based on 2nd element of list item
            l_con_info.sort(utils.list_element_1_sort)

            # if sub_p ==1, here is where we create the l_subcon_info using l_con_info
            l_subcon_info = []
            if sub_p == 1:
                # compute the subcons
                for con_info in l_con_info:
                    con_no = con_info[3]
                    subcon = annot.d_con_no2subcon.get(con_no)
                    # keep the same format as the subcon_info even though start and end loc is the same for subcons.
                    l_subcon_info.append([subcon.loc, subcon.loc, con.type, con.no]) 

                # use the subcon list as the con_list
                l_con_info = l_subcon_info

            # for each concept, generate features and place them on the chart
            # keep track where we are in the list of l_con_info so we can compute next and 
            # prev concept locations.
            con_index = 0
            max_con_index = len(l_con_info) - 1
            for con_info in l_con_info:
                ###
                # con.display()
                # put this information in all edges spanned by the concept
                start = con_info[0]
                end = con_info[1]
                type = con_info[2]
                no = con_info[3]
                # for each column in the current concept's span
                # note we use end + 1 since the range does not include the end value
                #pdb.set_trace()
                for i in range(start, end + 1):
                    ###
                    # pdb.set_trace()
                    # print "i is %i" % i
                    current_col = self.col[i]
                    current_col.con_type = type 
                    current_col.con_no = no
                    current_col.con_start = start
                    current_col.con_end = end
                    # if there is a next con, store its info
                    if con_index < max_con_index:
                        next_con_info = l_con_info[con_index + 1]
                        current_col.next_con_start = next_con_info[0]
                        current_col.next_con_end = next_con_info[1]
                        current_col.next_con_type = next_con_info[2]
                        if current_col.next_con_type == current_col.con_type:
                            current_col.next_same_type_con_start = current_col.next_con_start
                    if con_index > 0:
                        prev_con_info = l_con_info[con_index - 1]
                        current_col.prev_con_start = prev_con_info[0]
                        current_col.prev_con_end = prev_con_info[1]
                        current_col.prev_con_type = prev_con_info[2]
                        if current_col.prev_con_type == current_col.con_type:
                            current_col.prev_same_type_con_start = current_col.prev_con_start

                con_index += 1


    # find location of the nearest lemma instance with given value (either to left or right)
    def nearest_lemma(self, lemma, start_col, dir):
        # return -1 is lemma is not found
        lemma_found_in_col = -1
        col = start_col
        if dir == "l":
            col = col - 1
            while col >= 0 and self.col[col].lemma != lemma:
                col = col - 1
            if col > -1:
                # lemma was found
                lemma_found_in_col = col
        if dir == "r":
            col = col + 1
            while col <= self.max and self.col[col].lemma != lemma:
                col = col + 1
            if col <=  self.max:
                # lemma was found
                lemma_found_in_col = col
        return(lemma_found_in_col)

    # find location of the nearest part of speech instance with given value (either to left or right)
    # matching is by first char in pos  (e.g. VBZ => V)
    def nearest_pos(self, pos, start_col, dir):
        # return -1 is pos is not found
        pos_found_in_col = -1
        col = start_col
        if dir == "l":
            col = col - 1
            while col >= 0 and self.col[col].pos[0:1] != pos[0:1]:
                col = col - 1
            if col > -1:
                # pos was found
                pos_found_in_col = col
        if dir == "r":
            col = col + 1
            while col <= self.max and self.col[col].pos[0:1] != pos[0:1]:
                col = col + 1
            if col <=  self.max:
                # pos was found
                pos_found_in_col = col
        return(pos_found_in_col)

    def count_lemma_instances(self, lemma):
        count = 0
        col_no = 0
        for col in self.col:
            if self.col[col_no].lemma == lemma:
                count += 1
            col_no += 1
        return(count)

    def count_con_type(self, con_type):
        count = 0
        col_no = 0
        for col in self.col:
            if self.col[col_no].con_type == con_type:
                count += 1
            col_no += 1
        return(count)

            
    # return the type of conjunction: and, or, comma, ""
    def coord_conj_type(self, col_no):
        lemma_before = ""
        first = -1
        last = -1
        conjunctions = ["and", "or", ","]
        # To find out if we are part of a coordination, we have to run
        # coord_con_first and coord_con_last
        first = self.coord_con_first(col_no)
        last = self.coord_con_last(col_no)
        if first == -1 and last == -1:
            # not a coordination
            return ""
        if last == -1:
            # col_no must already be last
            # make sure we get the first col in the last concept
            last = self.coord_con_last(first)
        # now find the lemma just before last
        # print "[coord_conj_type] last_loc: %i" % (last)
        # get the lemma of the col prior to last_loc
        if last > 0:
            lemma_before = self.col[last - 1].lemma
            # print "[coord_conj_type] last: %i, lemma_before: %s" % (last, lemma_before)
            if lemma_before not in conjunctions:
                lemma_before = ""
            else:
                if lemma_before == ",":
                    lemma_before = "comma"
        return(lemma_before)
                

    # find the start loc of the first concept of same type as concept in col_no in what is likely
    # a coordinate structure
    def coord_con_first (self, col_no, conjunction_list = "all"):
        conjunctions = ""
        if conjunction_list == "all":
            conjunctions = ["and", "or", "also", ","]
        else:
            # for some lists, modifiers (e.g. negatives) don't cross comma boundaries
            conjunctions = ["and", "or", "also" ]
            
        # keep track of the start of the last (coordinate) concept visited
        last_con_start = self.col[col_no].con_start
        current_col = col_no - 1
        # flag to indicate whether we are still in a potential coordinate situation
        still_looking = 1
        con_type = self.col[col_no].con_type
        if con_type == "":
            # this column does not hold a concept, so return -1
            return(-1)
        else:
            
            # iterate through any previous coordinated phrases of the same type
            # Depending on conjunction_list, 
            # we keep looking as long as we see one of comma (_C_), concept, or conj (and, or, also)
            while current_col >= 0 and still_looking == 1:
                if self.col[current_col].con_type == con_type:
                    last_con_start = self.col[current_col].con_start
                elif self.col[current_col].lemma not in conjunctions:
                    still_looking = 0
                current_col = current_col - 1
        # if there was a previous coordinate, its start will be in last_con_start.  
        # if it is not different from the original concept start, then return -1
        # else return the start loc of the earliest coordinated concept
        if last_con_start != self.col[col_no].con_start:
            return(last_con_start)
        else:
            return(-1)

    # find the end loc of the last concept of same type as concept in col_no in what is likely
    # a coordinate structure
    def coord_con_last (self, col_no, conjunction_list = "all"):
        conjunctions = ""
        if conjunction_list == "all":
            conjunctions = ["and", "or", "also", ","]
        else:
            # for some lists, modifiers (e.g. negatives) don't cross comma boundaries
            conjunctions = ["and", "or", "also" ]

        # keep track of the start of the last (coordinate) concept visited
        last_con_end = self.col[col_no].con_end
        current_col = col_no + 1
        # flag to indicate whether we are still in a potential coordinate situation
        still_looking = 1
        con_type = self.col[col_no].con_type
        if con_type == "":
            # this column does not hold a concept, so return -1
            return(-1)
        else:
            
            # iterate through any previous coordinated phrases of the same type
            # we keep looking as long as we see one of comma (_C_), concept, or conj (and, or, also)
            while current_col <= self.max and still_looking == 1:
                if self.col[current_col].con_type == con_type:
                    last_con_end = self.col[current_col].con_end
                elif self.col[current_col].lemma not in conjunctions:
                    still_looking = 0
                current_col = current_col + 1
        # if there was a previous coordinate, its start will be in last_con_start.  
        # if it is not different from the original concept start, then return -1
        # else return the start loc of the earliest coordinated concept
        if last_con_end != self.col[col_no].con_end:
            return(last_con_end)
        else:
            return(-1)

    # special case for sentence containing a hypothetical
    def sent_hypothetical_p(self):
        for col in self.col:
            if term_hypothetical_p(col.lemma):
                return(1)
        return(0)

    # special case for sentence containing a family term
    def sent_family_p(self):
        for col in self.col:
            if term_family_p(col.lemma):
                return(1)
        return(0)

    def sent_negative_p(self):
        for col in self.col:
            if term_negative_p(col.lemma):
                return(1)
        return(0)                




    # NOT FINISHED
    # This could be useful for the concept identification task.  For the other tasks,
    # there is no guarantee that the sdparser will treat a concept as a single NP
    # so we can't really depend on it for finding the head.  Instead, it is better to use
    # the subtxt for doing sdp features since each concept corresponds to a single chart col.
    def con_head(self, col_no):
        # get the start token within the concept
        con_start = self.col[col_no].con_start
        con_no = self.col[col_no].con_no
        current_col = con_start
        # flag to indicate whether we are still in a potential coordinate situation
        still_looking = 1
        con_type = self.col[col_no].con_type
        if con_type == "":
            # this column does not hold a concept, so return -1
            return(-1)
        else:
            print "not finished///"

    # col_no is index in the chart, starting at 0
    # dir is {"l", "r")
    # length is an integer stating the size of the ngram
    # concepts count as a single token
    # distance is an integer stating how far to the left or right this ngram should start
    # 1 is adjacent.
    # lemma_p = {0, 1} : whether to use lemma rather than token
    # if semcat_p = 1, use the semcat rather than the lemma, if there is one
    def ngram(self, dir, col_no, length, lemma_p, distance = 1, semcat_p = 0, bound_col = -1):
        # print "[ngram]distance: %i, col_no: %i, length: %i, lemma_p: %i" % (distance, col_no, length, lemma_p)
        current_ngram_lenth = 0
        ngram = ""
        token = ""
        # list of columns to include in ngram
        ngram_col_list = []
        current_col_no = col_no

        # flag to indicate if a non-empty semcat was encountered while matching patterns
        semcat_found_p = 0
        
        if dir == "r":
            # determine right bound
            if bound_col == -1:
                # bound is end of chart
                bound_col = self.max
            # determine start location
            current_col_no = current_col_no + distance
            # print "[ngram r] start loc: %i" % current_col_no
            while current_col_no <= self.max and current_col_no <= bound_col and len(ngram_col_list) < length:
                # add column to ngram_col_list
                #print "[ngram] current_col_no: %i, self.max: %i" % (current_col_no, self.max)
                ngram_col_list.append(current_col_no)
                if self.col[current_col_no].con_type != "":
                    # advance current_col_no past the current concept
                    # We count the concept as a single token
                    current_col_no = self.col[current_col_no].con_end + 1
                else:
                    # increment the current_col_no
                    current_col_no = current_col_no + 1

        else:
            # dir = "l"
            # determine left bound
            if bound_col == -1:
                # bound is start of chart
                bound_col = 0
            # determine start location
            current_col_no = current_col_no - distance
            # print "[ngram l] start loc: %i" % current_col_no
            while current_col_no >= 0 and current_col_no >= bound_col and len(ngram_col_list) < length:
                # add column to ngram_col_list
                ngram_col_list.append(current_col_no)
                if self.col[current_col_no].con_type != "":
                    # advance current_col_no before the current concept
                    # We count the concept as a single token
                    current_col_no = self.col[current_col_no].con_start - 1
                    # print "in left pass concept: current_col_no: %i" % current_col_no
                else:
                    # decrement the current_col_no

                    current_col_no = current_col_no - 1
                    # print "in left decrement: current_col_no: %i" % current_col_no
                    
                    
        # Now check if the desired ngram length has been satisfied
        if len(ngram_col_list) == length:
            # create the ngram string
            ## print "ngram_col_list: %s" % ngram_col_list 
            # if dir is "l", we need to reverse the ngram list first to order it left to right
            if dir == "l":
                # reverse works on list in place
                ngram_col_list.reverse() 
            for col_no in ngram_col_list:
                # determine the string to be added to the ngram
                if semcat_p == 1 and self.col[col_no].semcat != "":
                    token = self.col[col_no].semcat
                    ## print "semcat for col %i: %s" % (col_no, token)
                    semcat_found_p = 1
                    
                elif self.col[col_no].con_type != "":
                    # replace concepts with its type preceded by ^ (e.g. ^PROBLEM)
                    token = "^" + self.col[col_no].con_type.upper()

                elif lemma_p == 1:
                    token = self.col[col_no].lemma
                else:
                    token = self.col[col_no].token.lower()

                ngram = ngram + "_" + token
                # print "[ngram checked] col_no: %i, ngram: %s" % (col_no, ngram)

        # remove the initial "_" from the ngram
        # note: ngram is "" if conditions are not met
        # if semcat_p is set, only return the ngram if it includes a semcat
        if semcat_p != 1 or semcat_found_p == 1:
            return(ngram[1:])
        else:
            return("")

    # returns a list of ngrams
    # length_list: a list of integers indicating ngram lengths desired
    # window: an integer indicating the distance of the ngrams from col_no
    # lemma_p: if 1, returns lemma rather than surface string
    # semcat_p: if 1, returns semcat rather than lemma, if there is one
    # bound_col is a col which bounds the region of the chart to consider.
    # if -1, there is n bound.  Otherwise, bound_col should be the first or last
    # col_no outside of the region, depending on direction.  A bound_col of 2 given
    # direction "l" asserts that only items from chart column 3 up should be considered.

    # Note that the outer loop s the distance from the target term.  This means that
    # ngrams will be ordered by proximity to the target
    def ngrams(self, dir, col_no, length_list, lemma_p, window, semcat_p = 0, bound_col = -1):
        ngram_list = []
        # add 1 to distance since it will be used in range expression as end of range
        distance_threshold = window + 1
        for distance in range(1, distance_threshold):
            for ngram_length in length_list:
                ngram = self.ngram(dir, col_no, ngram_length, lemma_p, distance, semcat_p, bound_col)
                if ngram != "" and (ngram not in ngram_list):
                    ngram_list.append(ngram)
        return(ngram_list)


    # start_col_no and end_col_no bound the region but are not included in ngrams
    def ngrams_between(self, start_col_no, end_col_no, length_list, lemma_p, semcat_p = 0):  
        ngram_list = []
        
        distance_threshold = (end_col_no - start_col_no)
        for distance in range(1, distance_threshold):
            for ngram_length in length_list:
                if start_col_no + distance + ngram_length <= end_col_no:
                    ngram = self.ngram("r", start_col_no, ngram_length, lemma_p, distance, semcat_p)
                    if ngram != "":
                        ngram_list.append(ngram)
        return(ngram_list)

    # dependency relations to be run on subtxt
    # col_no should be left or right most concept in cases of coordination
    # There can be more than one dominant node, so a list of chartdeps is returned

    # e.g. pred_list: ["prep_of1", ["dobj1", "nsubj0"] ]
    # pred is the sdp predicate with 0 or 1 appended, indicating the argument position of the 
    # source term in the predicate.
    def tdc_path(self, col_no, pred_path, dep_path = [], cols_visited = []):
        # keep a queue of matches in progress
        stack = [[col_no, pred_path, dep_path, cols_visited]]
        # keep successful matches
        matches = []
        # do not allow loops
        # pdb.set_trace()
        deps = []
        while stack != []:
            item = stack.pop()
            col_no = item[0]
            pred_path = item[1]
            dep_path = item[2]
            cols_visited = item[3]
            if col_no not in cols_visited:
                # find matches for the next predicate in pred_path
                l_pred = pred_path.pop(0)
                # test if the pred is singleton or list
                # if not a list, make it one to simplify code
                if type(l_pred) != type([]):
                    l_pred = [l_pred]

                # now get all the chartdeps associated with this col_no
                deps = self.col[col_no].tdc_deps

                for dep in deps:
                    if dep.pred in l_pred:
                        # create copies of lists to add to the stack
                        new_pred_path = pred_path[:]
                        new_dep_path = dep_path[:]
                        new_dep_path.append(dep)
                        new_cols_visited = cols_visited
                        new_cols_visited.append(col_no)
                        if new_pred_path == []:
                            # then we have completed a match
                            matches.append(new_dep_path)
                        else:
                            # add the remainder of the pattern state to the stack
                            stack.append([dep.target_index, new_pred_path, new_dep_path, new_cols_visited])
        return(matches)

    # allows you to specify path and the coordinate concept to base the path on.  So, if a concept happens
    # to be in a coordinate construction, you can request that the pattern start with left most or right most
    # coordinate concept.
    # coord_pos: { "f", "l", "s" } for first, last, same 
    # This resets the start col_no before running the pattern.  "s" simply uses the col_no given
    # This should be used only with subtxt sentences, since they have one term per concept.
    def tdc_path_coord(self, col_no, pred_path, dep_path = [], cols_visited = [], coord_pos = "s"):
        revised_col_no = col_no
        # pdb.set_trace()
        if coord_pos == "f":
            revised_col_no = self.coord_con_first(col_no)
        elif coord_pos == "l":
            revised_col_no = self.coord_con_last(col_no)
        # if there is no coordinate concept, then use the col_no of the original concept
        if revised_col_no == -1:
            revised_col_no = col_no 
        matches = self.tdc_path(revised_col_no, pred_path, dep_path, cols_visited)
        return(matches)

    def tdc_path_lemma(self, path, path_index):
        dep = path[path_index]
        col_no = dep.target_index
        lemma = self.col[col_no].lemma
        return(lemma)

    # returns list of col_no's where a lemma of type pos occurs between the start and end cols.
    # pos can be any SDP POS tag or substring.  So pos of "N" will
    # match "NN" and "NNS"
    # returns empty list if no matches
    def pos_between_list(self, b_region_start, b_region_end, pos_prefix):
        pos_loc_list = []
        pos_match_p = 0
        for col_no in range((b_region_start + 1), (b_region_end -1)):
            pos =  self.col[col_no].pos
            if pos[0:len(pos_prefix)] == pos_prefix:
                pos_match_p = 1
                pos_loc_list.append(col_no)
        #return(pos_match_p)
        return(pos_loc_list)


    def pos_between_p(self, b_region_start, b_region_end, pos_prefix):
        pos_match_p = 0
        for col_no in range((b_region_start + 1), (b_region_end -1)):
            pos =  self.col[col_no].pos
            if pos[0:len(pos_prefix)] == pos_prefix:
                pos_match_p = 1
        return(pos_match_p)

    # return true if some lemma in lemma_list occurs in chart between start and end of region.
    def lemma_between_p(self, b_region_start, b_region_end, lemma_list):
        lemma_match_p = 0
        for col_no in range((b_region_start + 1), (b_region_end -1)):
            lemma =  self.col[col_no].lemma
            if lemma in lemma_list:
                lemma_match_p = 1
        return(lemma_match_p)



# creates an in memory representation for an arff file
class Arff:
    def __init__(self, arff_file):
        # dict to map weka attr number (0 based) to attr name
        self.d_attr_no = {}
        self.d_data_no = {}
        # list of attr names
        self.l_attrs = []
        s_arff = open(arff_file, "r")
        
        # weka bases attributes on 0
        # data instances on 1
        attr_no = 0
        data_no = 1
        for line in s_arff:
            line = line.strip("\n")
            line = line.lstrip(" ")
            # attribute line
            line_len = len(line)
            # Note that weka generated arff files use lowercased "@attribute"
            # to introduce attribute names
            if line_len > 6 and (line[0:5] == "@ATTR" or line[0:5] == "@attr"):
                attr_name = self.attr_name_from_arff_line(line)
                self.d_attr_no[attr_no] = attr_name
                self.l_attrs.append(attr_name)
                attr_no += 1
            
            # data line
            elif line_len > 3 and line[0] == "{":
                feature_list = self.data_line2list(line)
                self.d_data_no[data_no] = feature_list
                data_no += 1
            
        s_arff.close()

    # return a human readable string of attr value pairs for an instance
    def feature_string(self, data_no):
        print_string = ""
        feature_list = self.d_data_no.get(data_no)
        for (attr_no, value) in feature_list:
            attr_string = self.d_attr_no.get(attr_no)
            print_string = print_string + attr_string + " " + value + ", "
        return(print_string)

    def inspect(self, data_no, annot, annot_type, vert="1"):
        feature_string = self.feature_string(data_no)
        txt_no = 0
        if annot_type == "ast":
            # note the annotations are 0- based
            ast = annot.d_ast_no.get(data_no - 1)
            ast.inspect()
            txt_no = ast.txt_no
        elif annot_type == "rel":
            rel = annot.d_rel_no.get(data_no - 1)
            rel.inspect()
            txt_no = rel.txt_no

        print "[TXT] %s" % annot.d_txt_no.get(txt_no).line
        print "[SUB] %s" % annot.d_txt_no2subtxt.get(txt_no).line.strip(" ")
        if vert == "0":
            print "%i: %s" % (data_no, feature_string)        
        else:
            # print features as vertical list
            # add an initial space so items line up.
            print "",
            items = feature_string.split(",")
            for item in items:
                print item

    def attr_name_from_arff_line(self, line):
        # Get the line starting after @ATTRIBUTE
        rest = line[11:]
        # remove extra ws
        rest.lstrip(" ")
        name = rest[0:rest.find(" ")]
        return(name)

    def data_line2list(self, line):
        feature_list = []
        # print "[data_line] line: %s" % line
        line = line.strip("{ }")
        items = line.split(",")
        for item in items:
            item = item.strip(" ")
            # print "[data_line]item: %s" % item
            (attr_no, value) = item.split(" ")
            feature_list.append([int(attr_no), value])
        return(feature_list)

# routines for creating system output files with predictions        
def get_weka_prediction_list(weka_pred_file):
    # read the predictions
    s_pred = open(i2b2_config.weka_dir + weka_pred_file, "r")
    # Flag to indicate when we have reached the prediction section of
    # the input file
    pred_section_p = 0
    l_preds = []

    for line in s_pred:
        line = line.strip("\n ")
        # pdb.set_trace()
        if pred_section_p == 0:
            if line[0:5] == "inst#":
                # The next line will start the predictions
                pred_section_p = 1
        else:
            # we're in the prediction section
            # each line has multi-blank separated fields
            # error, indicated by "+" is blank if absent
            # So we will split the line on blanks and keep the
            # first 4 fields.  If the last field starts with "+"
            # then we know it's an error
            fields = line.split()
            # check if we are finished with the prediction section
            if len(fields) == 0:
                pred_section_p = 0
            else:
                # process prediction line
                # convert instance number to 0 base
                # to be consistent with annotation number
                # in Annotations instance
                instance_no = int(fields[0]) - 1
                actual_fields = fields[1].split(":")
                actual = actual_fields[1]
                predicted_fields = fields[2].split(":")
                predicted = predicted_fields[1]
                rest = fields[3]

                # keep track of prediction for this instance
                l_preds.append( predicted )

    
    s_pred.close()
    return(l_preds)


# added mallet version 1/19/11 PGA  ////
# routines for creating system output files with predictions
# WARNING: This only works for output from test files in which all lines of the
# test file are predicted.  That is, the csvline must start with 1 and proceed in sorted order.
# e.g. rel.17.res.stdout
def get_mallet_prediction_list(mallet_pred_file):
    # read the predictions
    s_pred = open(i2b2_config.mallet_dir + mallet_pred_file, "r")
    l_preds = []

    i = 1
    for line in s_pred:
        line = line.strip("\n ")
        # pdb.set_trace()
        # Test for prediction line
        if line[0:7] == "csvline":
            fields = line.split(" ")
            line_info = fields[0]
            line_no = line_info.split(":")[1]
            if i != int(line_no):
                print "ERROR: file is not a sequence of csvlines starting at 1"
            actual = fields[1]
            predicted = fields[2].split(":")[0]
            print "line_no: %s, actual: %s, predicted: %s" % (line_no, actual, predicted)
            l_preds.append( predicted )
            i = i + 1
            
    s_pred.close()
    return(l_preds)

# When we run maxent over unlabeled data, we get a different output than for labeled data.
# This output is passed through mallet_condense_classify_output.py to produce lines of
# the form:
# 0 present       present 0.957410066193  conditional 0.0195004978702 ...
# The prediction is the second field of the first tab separated field.

# e.g. python mallet_condense_classify_output.py < ast.75.res.stdout > ast.75.maxent.pred
def get_mallet_condensed_prediction_list(mallet_pred_file):
    # read the predictions
    s_pred = open(i2b2_config.mallet_dir + mallet_pred_file, "r")
    l_preds = []

    i = 1
    for line in s_pred:
        line = line.strip("\n ")
        # pdb.set_trace()
        fields = line.split("\t")
        prediction = fields[0].split(" ")[1]
        l_preds.append( prediction )
        i = i + 1
            
    s_pred.close()
    return(l_preds)

    
class Prediction:
    def __init__(self, actual, predicted, instance_no):
        self.actual = actual
        self.predicted = predicted
        self.instance_no = instance_no
                                

# Object to aid in analysis of weka predictions,
# combining original arff file containing all attrs,
# arff created after attr selection, and
# prediction file


class Preds:
# e.g.
# preds = futils.Preds(a, "rel", "rel.8.arff", "rel.8.chi2_100.r0.c0.arff" , 'rel.8.chi2_100.r0.j48_2', "", "")

    def __init__(self, annot, annot_type, source_file, test_file,  classify_prefix, annot_rp = "", rp_type = ""):
        #pdb.set_trace()
        arff_source_file = i2b2_config.weka_dir + source_file
        arff_test_file = i2b2_config.weka_dir + test_file
        pred_file = i2b2_config.weka_dir + classify_prefix + ".pred"
        self.arff_source = Arff(arff_source_file)
        self.arff_test = Arff(arff_test_file)
        self.d_actual = {}
        self.d_actual_pred = {}
        # given instance_no, return the prediction
        self.d_instance_pred = {}
        self.annot_type = annot_type
        self.annot = annot
        self.annot_rp = annot_rp
        self.rp_type = rp_type
        print "[preds] rp_type: %s" % self.rp_type
        # name of the classify arff file without the .arff
        self.classify_prefix = classify_prefix
        self.test_file = test_file
        
        # read the predictions
        s_pred = open(pred_file, "r")
        print "[preds] Reading predictions from %s" % pred_file
        # Flag to indicate when we have reached the prediction section of
        # the input file
        pred_section_p = 0

        for line in s_pred:
            line = line.strip("\n ")
            # pdb.set_trace()
            if pred_section_p == 0:
                if line[0:5] == "inst#":
                    # The next line will start the predictions
                    pred_section_p = 1
            else:
                # we're in the prediction section
                # each line has multi-blank separated fields
                # error, indicated by "+" is blank if absent
                # So we will split the line on blanks and keep the
                # first 4 fields.  If the last field starts with "+"
                # then we know it's an error
                fields = line.split()
                # check if we are finished with the prediction section
                if len(fields) == 0:
                    pred_section_p = 0
                else:
                    # process prediction line
                    # convert instance number to 0 base
                    # to be consistent with annotation number
                    # in Annotations instance
                    instance_no = int(fields[0]) - 1
                    actual_fields = fields[1].split(":")
                    actual = actual_fields[1]
                    predicted_fields = fields[2].split(":")
                    predicted = predicted_fields[1]
                    rest = fields[3]

                    # keep track of prediction for this instance
                    self.d_instance_pred[instance_no] = predicted
                    
                    if rest[0] == "+":


                        # it is a prediction error
                        # store it by actual and by predicted key
                        prediction = Prediction(actual, predicted, instance_no)
                        if self.d_actual.has_key(actual):
                            self.d_actual[actual].append(prediction)
                        else:
                            self.d_actual[actual] = [prediction]
                        actual_pred = actual + "_" +  predicted
                        if self.d_actual_pred.has_key(actual_pred):
                            self.d_actual_pred[actual_pred].append(prediction)
                        else:
                            self.d_actual_pred[actual_pred] = [prediction]
                    
        s_pred.close()


    # return a human readable string of attr value pairs for an instance
    def feature_string(self, data_no):
        print_string = ""
        feature_list = self.arff_source.d_data_no.get(data_no)
        for (attr_no, value) in feature_list:
            attr_string = self.arff_source.d_attr_no.get(attr_no)

            # test if the attr is in the selected arff
            # Mark NON-selected attrs with * in output
            if attr_string not in self.arff_test.l_attrs:
                attr_string = "* " + attr_string
            print_string = print_string + attr_string + " " + value + ", "
        return(print_string)


    def inspect(self, data_no):
        annot = self.annot
        annot_type = self.annot_type
        feature_string = self.feature_string(data_no)
        txt_no = 0
        if annot_type == "ast":
            # note the annotations are 0- based
            ast = annot.d_ast_no.get(data_no - 1)
            ast.inspect()
            txt_no = ast.txt_no
        elif annot_type == "rel":
            rel = annot.d_rel_no.get(data_no - 1)
            rel.inspect()
            txt_no = rel.txt_no

        elif annot_type == "rp":
            rp = self.annot_rp.d_relpair_no.get(data_no - 1)
            rp.inspect()
            txt_no = rp.txt_no

        else:
            print "[preds.inspect] Unknown annot type: %s" % annot_type
            
        print "txt: %s" % annot.d_txt_no.get(txt_no).line
        print "sub: %s" % annot.d_txt_no2subtxt.get(txt_no).line.strip(" ")
        # print features as vertical list
        # add an initial space so items line up.
        print "",
        items = feature_string.split(",")
        for item in items:
            print item

    def inspect_errors(self, data_no, s_errors):
        annot = self.annot
        annot_type = self.annot_type

        feature_string = self.feature_string(data_no)
        txt_no = 0
        # temporarily reset stdout to send the output
        # of the inspect calls to the s_errors stream
        sys.stdout = s_errors

        if annot_type == "ast":
            # note the annotations are 0- based
            ast = annot.d_ast_no.get(data_no - 1)
            ast.inspect()
            txt_no = ast.txt_no

        elif annot_type == "rel":
            rel = annot.d_rel_no.get(data_no - 1)
            rel.inspect()
            txt_no = rel.txt_no

        elif annot_type == "rp":
            # use the appropriate ordered list to get the rp corresponding
            # to the weka data_no
            txt_no = 0
            if self.rp_type == "treatment":
                rp = self.annot_rp.l_rp_treatment[data_no - 1]
                rp.inspect()
                txt_no = rp.txt_no            
            elif self.rp_type == "test":
                rp = self.annot_rp.l_rp_test[data_no - 1]
                rp.inspect()
                txt_no = rp.txt_no            
            elif self.rp_type == "problem":
                rp = self.annot_rp.l_rp_problem[data_no - 1]
                rp.inspect()
                txt_no = rp.txt_no            
            else:
                # we are using the entire list, not type specific
                rp = self.annot_rp.d_relpair_no.get(data_no - 1)
                rp.inspect()
                txt_no = rp.txt_no            


        # restore output
        sys.stdout = sys.__stdout__

        # pdb.set_trace()
        print "[inspect_errors] txt_no: %i" % txt_no
        s_errors.write("[TXT] %s\n" % annot.d_txt_no.get(txt_no).line)
        s_errors.write("[SUB] %s\n" % annot.d_txt_no2subtxt.get(txt_no).line.strip(" "))
        # print features as vertical list
        # add an initial space so items line up.
        s_errors.write("",)
        items = feature_string.split(",")
        for item in items:
            s_errors.write("%s\n" % item)

    def errors(self):
        annot = self.annot
        annot_type = self.annot_type
        error_file = i2b2_config.weka_dir + self.classify_prefix + ".errors"
        s_errors = open(error_file, "w")
        for key in self.d_actual_pred.keys():
            for pred in self.d_actual_pred.get(key):
                # adjust instance_no to arff, which is based on 1 instead of 0
                instance_no = pred.instance_no + 1
                s_errors.write( "--------------------------------------------------------\n")
                s_errors.write( "[%i] Actual: %s, Predicted: %s\n" % (instance_no, pred.actual, pred.predicted))
                self.inspect_errors(instance_no, s_errors)
        s_errors.close()

# print out grammatical sequences

def tag_match(annot, pattern, output):
    s_match = open(output, "w")
    for txt in annot.l_txt:
        txt_no = txt.no
        subchart = Chart(annot, txt_no, 1)
        for col in subchart.col:
            pos = col.pos
            lemma = col.lemma
            s_match.write( "%s\t%s\n" % (pos, lemma))

    s_match.close()


def affixes(token_list):
    affix_list = []
    for token in token_list:
        token_lower = token.lower()
        for affix in d_affixes.keys():
            if (len(token) - len(affix) > 2) and  token_lower.find(affix) > -1:
                affix_list.append(affix)
    return(affix_list)

def shared_terms(l_token_1, l_token_2, min_len):
    # lowercase and remove tokens with len < min_len
    l_token_1_filtered = []
    l_token_2_filtered = []
    for term in l_token_1:
        if len(term) > min_len:
            term = term.lower()
            l_token_1_filtered.append(term)
    for term in l_token_2:
        if len(term) > min_len:
            term = term.lower()
            l_token_2_filtered.append(term)
    return(utils.intersect(l_token_1_filtered, l_token_2_filtered))

# given two lists of tokens, returns a list of stems of stem_len chars that appear in both lists
def shared_stems(l_token_1, l_token_2, stem_len):
    # we will keep the first stem_length characters
    # lowercase and remove tokens with len <= stem_len
    l_token_1_filtered = []
    l_token_2_filtered = []
    for term in l_token_1:
        if len(term) > stem_len:
            term = term.lower()[0:stem_len]
            l_token_1_filtered.append(term)
    for term in l_token_2:
        if len(term) > stem_len:
            term = term.lower()[0:stem_len]
            l_token_2_filtered.append(term)
    return(utils.intersect(l_token_1_filtered, l_token_2_filtered))



def shared_affixes(l_token_1, l_token_2):
    # lowercase and remove tokens with len < min_len
    l_token_1_affixes = affixes(l_token_1)
    l_token_2_affixes = affixes(l_token_2)
    return(utils.intersect(l_token_1_affixes, l_token_2_affixes))



# load the d_semcat dictionary
d_semcat = load_semcat()
d_affixes = load_affixes()
# feature generalizations
d_fgen = load_fgen()
# noisewords
d_noise = load_noise()
        
# for testing lists
def filter_relpair_list(annot_rp, type):
    filtered_relpair_list = []
    for rp in annot_rp.relpair_list:
        if rp.c1.type == type:
            filtered_relpair_list.append(rp)
    return(filtered_relpair_list)

def filter_relpair_list_no(annot_rp, type):
    filtered_relpair_list = []
    for rp in annot_rp.relpair_list:
        if rp.c1.type == type:
            filtered_relpair_list.append(rp.no)
    return(filtered_relpair_list)


def l_rp_test_no(annot_rp):
    l_no = []
    for rp in annot_rp.l_rp_test:
        l_no.append(rp.no)
    return(l_no)

# diagnostic
# determine txt lines associated with a a rel class that contain a word

def find_word_in_rel_txt(annot, rel_class, word, lemma_p = 0):
    txt_list = []
    for rel in annot.l_rel:
        if rel_class == rel.rel:
            txt_no = rel.txt_no
            if word in annot.d_txt_no.get(txt_no).tokens:
                txt_list.append([rel, annot.d_txt_no.get(txt_no)])

    return(txt_list)

# remove words from a list if they contain fewer than min_len chars.
# Return the filtered list.
def filter_words_by_length (l_words, min_len):
    l_filtered = []
    for word in l_words:
        if len(word) >= min_len:
            l_filtered.append(word)
    return(l_filtered)

# remove words from a list if they contain fewer than min_len chars.
# Return the filtered list.
def filter_words_by_noise (l_words):
    l_filtered = []
    for word in l_words:
        if not d_noise.has_key(word):
            l_filtered.append(word)
    return(l_filtered)



# return concatenation of two words, in alpha sorted order (if alpha_p == 1)
def make_word_pair (w1, w2, alpha_p=1):
    wpair = ""
    if alpha_p == 0:
        wpair = w1 + "__" + w2
    else:
        if w1 < w2:
            wpair = w1 + "__" + w2
        else:
            wpair = w2 + "__" + w1
    return(wpair)

# diagnostic for PIP
# generate stats for cooccurrence of terms within PIP and NonePP relations
def rel_costats(annot):
    min_len = 5
    # word count within a problem field
    d_p_count = {}
    # pair of words cooccurring within PIP relation
    d_pip_count = {}
    # pair of words cooccurring within NonePiP relation
    d_nonepp_count = {}
    
    for rel in annot.l_rel:
        l_c1 = filter_words_by_length(rel.c1_string.split(" "), min_len)
        l_c2 = filter_words_by_length(rel.c2_string.split(" "), min_len)
        
        relation = rel.rel
        if relation == "PIP":
            for w1 in l_c1:
                w1 = w1.lower()
                if d_p_count.has_key(w1):
                    d_p_count[w1] = d_p_count.get(w1) + 1
                else:
                    d_p_count[w1] = 1

                for w2 in l_c2:
                    w2 = w2.lower()
                    if d_p_count.has_key(w2):
                        d_p_count[w2] = d_p_count.get(w2) + 1
                    else:
                        d_p_count[w2] = 1

                    # word cooccurrence pairs
                    wpair = make_word_pair(w1, w2)
                    if d_pip_count.has_key(wpair):
                        d_pip_count[wpair] = d_pip_count.get(wpair) + 1
                    else:
                        d_pip_count[wpair] = 1
                        
                    
        if relation == "NonePP":
            for w1 in l_c1:
                w1 = w1.lower()
                if d_p_count.has_key(w1):
                    d_p_count[w1] = d_p_count.get(w1) + 1
                else:
                    d_p_count[w1] = 1

                for w2 in l_c2:
                    w2 = w2.lower()
                    if d_p_count.has_key(w2):
                        d_p_count[w2] = d_p_count.get(w2) + 1
                    else:
                        d_p_count[w2] = 1

                    # word cooccurrence pairs
                    wpair = make_word_pair(w1, w2)
                    if d_nonepp_count.has_key(wpair):
                        d_nonepp_count[wpair] = d_nonepp_count.get(wpair) + 1
                    else:
                        d_nonepp_count[wpair] = 1
                        
                    
    # write out totals for word count within a problem field
    s_pc = open("p.c", "w")
    s_pipc = open("pip.c", "w")
    s_noneppc = open("nonepp.c", "w")
    for key in d_p_count.keys():
        s_pc.write( "%i %s\n" % (d_p_count.get(key), key))
    for key in d_pip_count.keys():
        s_pipc.write("%i %s\n" % (d_pip_count.get(key), key))
    for key in d_nonepp_count.keys():
        s_noneppc.write( "%i %s\n" % (d_nonepp_count.get(key), key))

    s_pc.close()
    s_pipc.close()
    s_noneppc.close()
    

# produce a list of all pairs of words, one from p1 and one from p2
# that are longer than min_len
def phrase_unigram_cross(p1, p2, min_len, alpha_p=1):
    pair_list = []
    l_c1 = filter_words_by_noise(p1.split(" "))
    l_c2 = filter_words_by_noise(p2.split(" "))
    for w1 in l_c1:
        w1 = w1.lower()
        for w2 in l_c2:
            w2 = w2.lower()
            # word cooccurrence pairs
            wpair = make_word_pair(w1, w2, alpha_p)
            pair_list.append(wpair)
    return(pair_list)
        

