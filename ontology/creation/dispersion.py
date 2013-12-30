# dispersion analysis

# use the  phr_feats file for a patent to generate frequency of phrases
# cd /home/j/anick/patent-classifier/ontology/creation/data/patents/ts500/data/d3_phr_feats/01/files/2000

# cat US6031898A.xml | egrep 'ABSTRACT|TITLE|SUMMARY' | cut -f3 | python /home/j/anick/patent-classifier/ontology/creation/dispersion.py | more

# input is in the form:
# phrase (in order of appearance in doc)
#e.g.
#calls
#authorization validations
#authorization validation

import sys
import collections
import utils

# phrase statistics for a doc
class Pstat:
    def __init__(self):

        # counts
        self.c_words = 0
        self.c_phrases = 0
        # number of word types in the doc
        self.c_word_types = 0
        # number of phrase types in the doc
        self.c_phr_types = 0

        # chunks containing a word
        # the length of the set is the dispersion of the word
        self.d_word2phr = collections.defaultdict(set)
        # number of occurrences of a phrase
        self.d_phr2count = collections.defaultdict(int)
        # number of times a word occurs in doc (within phrases)
        self.d_word2count = collections.defaultdict(int)
        # rank of a word (based on order of occurrence in doc)
        self.d_word2rank = collections.defaultdict(int)
        # rank of a phrase (based on order of occurrence in doc)
        self.d_phr2rank = collections.defaultdict(int)

    # phrase probability as the sum of probs of the component words
    def prob_phrase(self, phrase):
        summed_phrase_prob = 0
        phr_len = len(phrase)
        for word in phrase.split(" "):
            c_word = float(self.d_word2count[word])
            prob_word = c_word / self.c_words
            summed_phrase_prob += prob_word
            print "[rel_phrase]word: %s, rank: %i, prob: %0.3f" % (word, self.d_word2rank[word], prob_word)
        return(summed_phrase_prob)

    # relevance of a phrase is based on prob of component terms
    # and their relevance based on order of first appearance in a doc (rank)
    def rel_phrase(self, phrase):
        summed_phrase_rel = 0
        phr_len = len(phrase)
        for word in phrase.split(" "):
            c_word = float(self.d_word2count[word])
            prob_word = c_word / self.c_words
            # simple linear function for relevance of word
            word_rank_score = float(((self.c_word_types - self.d_word2rank[word]) + 1)) / self.c_word_types
            summed_phrase_rel += prob_word * word_rank_score
            print "[rel_phrase]word: %s, rank: %i, prob: %0.3f, word_rank_score: %0.3f" % (word, self.d_word2rank[word], prob_word, word_rank_score)

        phr_rank_score = float(((self.c_phr_types - self.d_phr2rank[phrase]) + 1)) / self.c_phr_types
        prob_phr = self.d_phr2count[phrase] / self.c_phrases
        print "[rel_phrase]phrase: %s, rank: %i, prob: %0.3f, phr_rank_score: %0.3f" % (phrase, self.d_phr2rank[phrase], prob_phr, phr_rank_score)

        phrase_score = summed_phrase_rel * phr_rank_score
        return(phrase_score)



    def read_phrase_file(self):
        for line in sys.stdin:

            phrase = line.strip("\n")
            
            self.d_phr2count[phrase] += 1
            self.c_phrases += 1
            #print "count: %i, phrase: %s" % (count, phrase)

            if not self.d_phr2rank.has_key(phrase):
                self.c_phr_types += 1
                self.d_phr2rank[phrase] = self.c_phr_types


            for word in phrase.split(" "):
                
                if not self.d_word2rank.has_key(word):
                    self.c_word_types += 1
                    self.d_word2rank[word] = self.c_word_types
                self.d_word2phr[word].add(phrase)
                self.d_word2count[word] += 1
                self.c_words += 1
            #print "d_word2phr[%s]: %s,count: %i" % (word, self.d_word2phr[word], self.d_word2count[word])
    
    def dispersion(self):
        for word in self.d_word2phr.keys():
            dispersion = len(self.d_word2phr[word])
            count = self.d_word2count[word]

            print "%s\t%i\t%i\t%s" % (word, count, dispersion, self.d_word2phr[word]) 
            
    def phrase_probs(self):
        l_phr_prob = []
        for phrase in self.d_phr2count.keys():
            phr_prob = self.prob_phrase(phrase)
            l_phr_prob.append([phrase, phr_prob])
        l_phr_prob.sort(utils.list_element_2_sort)
        for item in l_phr_prob:
            print item

    def phrase_rels(self):
        l_phr_rel = []
        for phrase in self.d_phr2count.keys():
            phr_rel = self.rel_phrase(phrase)
            l_phr_rel.append([phrase, phr_rel])
        l_phr_rel.sort(utils.list_element_2_sort)
        for item in l_phr_rel:
            print item




pstat = Pstat()
pstat.read_phrase_file()
pstat.dispersion()
#pstat.phrase_probs()
#pstat.phrase_rels()

    
