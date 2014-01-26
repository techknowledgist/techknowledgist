"""

Simple tool to take a file with terms and contexts, display the term in
context and sollicit whether the term is a technology. Usage:

% python technology_annotator.py <SOURCE_FILE> <LABELS_FILE>

The LABELS_FILE typically does not exist the first time you run the tool and it
will be created. In subsequent calls the LABELS_FILE will be opened and new
labels will be appended.

The annotator sees one term with its instances and then either hits 'y' or 'n'
followed by a return, where 'y' indicates that the term is a technology. The
tool appends a line to LABELS_FILE with a label and the term (tab-separated)
where the label is 'y' if the user replied 'y' and 'n' in any other case. Simply
hitting the return will add the 'n' label. Hitting 'q' followed by return closes
the files and saves the work. The tool remembers where it stopped last time and
will not simply start at the beginning when a file is reopened.

The SOURCE_FILE contains a list of terms where each term is printed as follows:

term
     year term_instance_id1 term_loc left_context term right_context
     year term_instance_id2 term_loc left_context term right_context
     ...

That is, the term on a line by itself, followed by one or more term instances
with their context. Each term instance line starts with a tab and all field are
tab-separated. See annotate.terms.context.txt for an example, this file was
created by the technology annotation code in step3_annotation.py.

"""

import os, sys, codecs, textwrap

BOLD = '\033[1m'
GREEN = '\033[32m'
BLUE = '\033[34m'
INV = '\033[97;100m'
END = '\033[0m'


def red_annotated_terms(out_file):
    annotated_terms = {}
    if os.path.exists(out_file):
        fh = codecs.open(out_file, encoding='utf-8')
        #done = len(fh_out.readlines())
        for line in fh:
            (label, term) = line.rstrip("\n\r").split("\t")
            annotated_terms[term] = True
        fh.close()
    return annotated_terms

def read_terms_with_contexts(fh_contexts):
    terms = []
    term = None
    contexts = []
    for line in fh_contexts:
        if line[0] == "\t":
            fields = line.strip().split("\t")
            contexts.append(fields)
        elif line.strip():
            if contexts:
                terms.append([term, contexts])
                contexts = []
            term = line.strip()
        else:
            print "WARNING:", line,
    if term is not None and contexts:
        terms.append([term, contexts])
    return terms

def print_term(term, contexts):
    print "\n%s%s%s\n" % (BOLD, term, END)
    for year, id, loc, left, t, right in contexts[:5]:
        print "   %s%s %s %s%s" % (GREEN, year, id, loc, END)
        lines = textwrap.wrap("%s %s%s%s %s\n" % (left, BLUE + BOLD, t, END, right), width=80)
        for l in lines: print '  ', l
        print

def process_answer(answer, fh_contexts, fh_labels):
    if answer == 'q':
        fh_contexts.close()
        fh_labels.close()
        exit("\n")
    elif answer == 'y':
        fh_labels.write("y\t%s\n" % term)
    else:
        fh_labels.write("n\t%s\n" % term)
    fh_labels.flush()

        
if __name__ == '__main__':

    contexts_file = sys.argv[1]
    labels_file = sys.argv[2]
    annotated_terms = red_annotated_terms(labels_file)
    fh_contexts = codecs.open(contexts_file, encoding='utf-8')
    fh_labels = codecs.open(labels_file, 'a', encoding='utf-8')

    terms = read_terms_with_contexts(fh_contexts)
    print "# Contexts file  -  %s" % contexts_file
    print "# Labels file    -  %s" % labels_file
    print "#"
    print "# Terms in contexts file  -  %d" % len(terms)
    print "# Previously annotated    -  %d\n" % len(annotated_terms)

    for term, contexts in terms:
        if term in annotated_terms:
            continue
        print_term(term, contexts)
        query = "Technology? (y) yes, (n) no, (q) quit\n? "
        answer = raw_input(query)
        process_answer(answer, fh_contexts, fh_labels)

