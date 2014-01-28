"""

Simple tool to take a file with terms and contexts, display the term in
context and sollicit whether the term is a technology. Usage:

% python technology_annotator.py <SOURCE_FILE>

The SOURCE_FILE has to be named *.context.txt. The first time you open
SOURCE_FILE, a new file will be created with the name *.labels.txt. Initially
this labels file is empty except for a header copied from SOURCE_FILE. The label
file will be opened on subsequent visits to the file. SOURCE_FILE is only read
and never written to.

The annotator sees one term with its instances and then either hits 'y', 'n' or
'c', followed by a return, where 'y' indicates that the term is a technology,
'n' indicates that the term is not a technology and 'c' indicates that the term
is corrupted. The tool appends a line to the labels file with a label and the
term. The default is to use 'n' for the label so simply hitting the return will
add the 'n' label. Hitting 'q' followed by return terminates annotation and
closes the files. The tool remembers where it stopped last time and will not
simply start at the beginning when a file is reopened.

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


def read_annotated_terms(out_file):
    annotated_terms = {}
    if os.path.exists(out_file):
        fh = codecs.open(out_file, encoding='utf-8')
        for line in fh:
            if line.startswith('#'):
                continue
            (label, term) = line.rstrip("\n\r").split("\t")
            annotated_terms[term] = True
        fh.close()
    return annotated_terms

def read_terms_with_contexts(fh_contexts):
    terms = []
    term = None
    info = ''
    contexts = []
    for line in fh_contexts:
        if line.startswith('#'):
            info += line
        elif line[0] == "\t":
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
    return info, terms

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
    elif answer == 'c':
        fh_labels.write("c\t%s\n" % term)
    else:
        fh_labels.write("n\t%s\n" % term)
    fh_labels.flush()


if __name__ == '__main__':

    contexts_file = sys.argv[1]
    if not contexts_file.endswith('.context.txt'):
        exit('ERROR: annotation file needs to end in ".context.txt".')
    labels_file = contexts_file.replace('.context.txt', '.labels.txt')

    annotated_terms = read_annotated_terms(labels_file)
    fh_contexts = codecs.open(contexts_file, encoding='utf-8')
    info, terms = read_terms_with_contexts(fh_contexts)

    print "\n### Contexts file  -  %s" % contexts_file
    print "### Labels file    -  %s" % labels_file
    print "###"
    print "### Terms in contexts file  -  %d" % len(terms)
    print "### Terms in labels file    -  %d\n" % len(annotated_terms)

    add_preface = False if os.path.exists(labels_file) else True
    fh_labels = codecs.open(labels_file, 'a', encoding='utf-8')
    if add_preface:
        fh_labels.write(info)
        fh_labels.flush()

    for term, contexts in terms:
        if term in annotated_terms:
            continue
        print_term(term, contexts)
        query = "Technology? (y) yes, (n) no, (c) crap/corrupted, (q) quit\n? "
        answer = raw_input(query)
        process_answer(answer, fh_contexts, fh_labels)

