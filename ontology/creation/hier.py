# Create a lexical hierarchy from a list of phrases
# 11/22/12 PGA

# phr_file is a file of phrases with no dups
# It can also be a file of phrase\tscore, created by 
# e.g.  cat utest.1.MaxEnt.out.avg_scores.nr | cut -f1,2 | grep '     0\.9' > utest.1.MaxEnt.out.avg_scores.nr.9


class Hier:
    def __init__(self, phr_file, out_file):
        self.d_phr = {}
        self.out_file = out_file
        # top of hierarchy contains a list of all top level phrases
        # These are phrases that have no "parent" (rightmost subphrase) in the phr_file
        self.top = []
        # populate the dict with phrases from phr_file
        s_phr = open(phr_file)
    
        # initialize dict with an empty list of children for each phrase
        for line in s_phr:
            line = line.strip()
            # extract the phrase from the line (anything before first tab)
            phr = line.split("\t")[0]
            self.d_phr[phr] = []

        s_phr.close()

    def create_hier(self):
        for phr in self.d_phr.keys():
            # create a list of words in a phrase
            l_phr = phr.split(" ")
            parent_found_p = False
            # subphrase of original phrase
            # which we will use to try to find a parent phrase
            phr_sub = phr

            while parent_found_p == False:
                # check for the longest rightmost subphrase (using " " as separator)
                subphrase_loc = phr_sub.find(" ") + 1
                if subphrase_loc == 0:
                    # No further subphrase exists, so this is a top level term
                    parent_found_p = True
                    self.top.append(phr)
                else:
                    # create longest rightmost subphrase
                    phr_sub = phr_sub[subphrase_loc:]
                    if self.d_phr.has_key(phr_sub):
                        # parent exists in dict
                        # make the current phrase a child of this parent
                        self.d_phr[phr_sub].append(phr)
                        #print "%s is a child of %s" % (phr, phr_sub)
                        parent_found_p = True
                    #else:
                        #print "No key found for: %s" % phr_sub
        

    # first call should use self.top (list of top level phrases) and indent of 0
    def print_hier(self, l_phr, indent, s_out):
        #print "About to sort l_phr: %s" % l_phr
        l_phr.sort()
        indent_size = 3

        # start with phrases in top, sorted alphabetically,
        # and do a depth first traversal of children
        for phr in l_phr:
            indent_string = " " * indent
            s_out.write(indent_string + phr + "\n")
            l_children = self.d_phr[phr]
            new_indent = indent + indent_size
            self.print_hier(l_children, new_indent, s_out)

    def print_all(self):
        # write output to out_file
        s_out = open(self.out_file, "w")

        #print "top: %s" % (self.top) 
        self.print_hier(self.top, 0, s_out)
        s_out.close()

def test():
    h = Hier("test.phr", "test.hier")
    print "Creating hier"
    h.create_hier()
    print "printing all"
    h.print_all()

# hierarchy for terms created with threshold of 0.9
def test_9():
    h = Hier("/home/j/anick/patent-classifier/ontology/creation/data/patents/en/test/utest.1.MaxEnt.out.avg_scores.nr.9", "en_9.hier")
    print "Creating hier"
    h.create_hier()
    print "printing all"
    h.print_all()

# hierarchy for terms created with threshold of 0.8
def test_8():
    h = Hier("/home/j/anick/patent-classifier/ontology/creation/data/patents/en/test/utest.1.MaxEnt.out.avg_scores.nr.8", "en_8.hier")
    print "Creating hier"
    h.create_hier()
    print "printing all"
    h.print_all()

