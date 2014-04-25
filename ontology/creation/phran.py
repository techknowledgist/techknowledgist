# phran.py
# phrasal analysis of heads and mods

# given a list of terms in a file
# return an instance of a phr_info object
# dict d_term2heads with key = term, value a list of heads occurring with the term
# dict d_term2mods with key = term, value a list of mods occurring with the term
# dict d_head2count with key = a term used as a head, value = count of terms it occurs with
# dict d_mod2count with key = a term used as a mod, value = count of terms it occurs with
# headed_term_count = # terms that appear with a head
# modified_term_count = # terms that appear with a modifier

import utils
from collections import defaultdict
import codecs

# p97 = phran.phrInfo("/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv/1997.t")

# term file should be a year file of the form: term category freq
# 

class phrInfo():
    def __init__(self, term_file):
        self.d_term2heads = defaultdict(list)
        self.d_term2mods =  defaultdict(list)
        self.d_head2terms = defaultdict(list)
        self.d_mod2terms =  defaultdict(list)
        self.d_head2count = defaultdict(int)
        self.d_mod2count = defaultdict(int)
        self.term_count = 0
        self.headed_term_count = 0
        self.modified_term_count = 0
        self.d_term_freq = defaultdict(int)
        self.d_term_cat = defaultdict(str)
        self.l_singletons = []
        # lists by category sorted by freq [[term, freq],...]
        self.l_c = []
        self.l_a = []
        self.l_t = []

        # open the file and import list of terms
        s_term_file = codecs.open(term_file, encoding='utf-8')
        for term_line in s_term_file:
            term_line = term_line.strip("\n")
            (term, cat, freq) = term_line.split("\t")
            freq = int(freq)
            self.d_term_freq[term] = freq
            self.d_term_cat[term] = cat
            self.term_count += 1
            if cat == "c":
                self.l_c.append([term, freq])
            elif cat == "t":
                self.l_t.append([term, freq])
            elif cat == "a":
                self.l_a.append([term, freq])

        s_term_file.close()

        # sort the category term lists
        self.l_c.sort(utils.list_element_2_sort)
        self.l_t.sort(utils.list_element_2_sort)
        self.l_a.sort(utils.list_element_2_sort)

        self.compute_heads_mods()

    def compute_heads_mods(self):
        for term in self.d_term_cat.keys():
            l_words = term.split(" ")
            if len(l_words) > 1:
                # term is a phrase.  Check for head and mod.
                term_no_mod = " ".join(l_words[1:])
                if self.d_term_freq.has_key(term_no_mod):
                    # Then subterm exists on its own
                    mod = l_words[0]
                    self.d_term2mods[term_no_mod].append(mod)
                    self.d_mod2terms[mod].append(term_no_mod)
                    self.modified_term_count += 1
                    self.d_mod2count[mod] += 1
                term_no_head = " ".join(l_words[0:len(l_words) - 1])
                if self.d_term_freq.has_key(term_no_head):
                    # Then subterm exists on its own
                    head = l_words[-1]
                    self.d_term2heads[term_no_head].append(head)
                    self.d_head2terms[head].append(term_no_head)
                    self.headed_term_count += 1
                    self.d_head2count[head] += 1
            else:
                # we have a single word term
                self.l_singletons.append(term)

    def sort_heads(self):
        l_head_counts = []
        for head in self.d_head2count.keys():
            l_head_counts.append([head, self.d_head2count[head]])
        l_head_counts.sort(utils.list_element_2_sort)
        return(l_head_counts)

# a98 = phran.phrInfo("/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv/1998.act.gt1")
# nt = phran.get_hf_terms(a06, a97, a98, "t")
# find terms with high freq in 2006 with 0 freq in 1997, 1998
def get_hf_terms(target_year_pi, ref_year1_pi, ref_year2_pi, cat):
    target_terms = []
    if cat == "c":
        target_terms = target_year_pi.l_c
    elif cat == "t":
        target_terms = target_year_pi.l_t
    elif cat == "a":
        target_terms = target_year_pi.l_a

    # new terms occur in target year and not in ref year
    # term_freq is a list of a term and its freq.
    l_new_terms = []
    for term_freq in target_terms:
         if (not ref_year1_pi.d_term_freq.has_key(term_freq[0])) and (not ref_year2_pi.d_term_freq.has_key(term_freq[0])):
             l_new_terms.append(term_freq)
    return(l_new_terms)
             

# to create the input file:
# cat 2006.act.cat.w0.0 | cut -f1,4,5 | egrep -v '  1$' > 2006.act.gt1
