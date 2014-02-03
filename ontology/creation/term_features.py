# term_features.py
# based on term_verb.py
# extract the term and prev_V value from phr_feats file
# lines are of the form:
# <term>\t<feature>+
# e.g.,
# message compiler        doc_loc=sent2   first_word=message      following_prep=for      last_word=compiler      next2_tags=IN_DT     next_n2=for_an  next_n3=for_an_object-oriented  prev_N=system   prev_V=including        prev_n2=including_a     prev_n3=system_including_a   section_loc=ABSTRACT_sent1      sent_loc=6-8    suffix3=ler     suffix4=iler    suffix5=piler   tag_sig=NN_NN

# output would be
# message compiler        prev_V=including

# If the line does not contain prev_V, nothing is output

# gunzip -c US5579518A.xml.gz | python /home/j/anick/patent-classifier/ontology/creation/term_verb.py | more
# | python /home/j/anick/patent-classifier/ontology/creation/term_verb.py | more

import sys

for line in sys.stdin:
    line = line.strip("\n")
    l_fields = line.split("\t")
    term = l_fields[2]
    for feature in l_fields[1:]:
        # Note that we use the prefixes of some feature names for convenience.
        # The actual features are prev_V, prev_J, prev_Jpr, prev_Npr, last_word
        if feature[0:6] in ["prev_V", "prev_J", "prev_N", "last_w"]:
            print "%s\t%s" % (term, feature)
