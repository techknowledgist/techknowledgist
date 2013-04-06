"""

Usage:
    
    % python patent_analyzer.py [OPTIONS]

    -l LANG      --  provides the language, one of ('en, 'de', 'cn'), default is 'en'
    -t PATH      --  target directory, default is data/patents
     
    --annotate1  --  prepare files for annotation of the prior
    --annotate2  --  prepare files for annotation for evaluation
    --verbose    --  
    

"""

import os, sys, time, shutil, getopt, subprocess, codecs, textwrap
from random import shuffle

import config_data
import putils

script_path = os.path.abspath(sys.argv[0])
script_dir = os.path.dirname(script_path)
os.chdir(script_dir)
os.chdir('../..')
sys.path.insert(0, os.getcwd())
os.chdir(script_dir)

# defaults that can be overwritten by command line options
source_path = config_data.external_patent_path
target_path = config_data.working_patent_path
language = config_data.language
verbose = False

    
def run_annotate1(target_path, language, limit):

    """Create input for annotation effort fro creating a prior. This function is different
    in the sense that it does not keep track of how far it got into the corpus. Rather,
    you tell it how many files you want to use and it takes those files off the top of the
    ws/phr_occ.all file and generates the input for annotation from there. And unlike
    --summary, this does not append to the output files but overwrites older versions. The
    limit is used just to determine how many files are taken to create the list for
    annotation, it is not used to increment any number in the ALL_STAGES.txt file."""
    
    phr_occ_all_file = os.path.join(target_path, 'ws', 'phr_occ.all')
    phr_occ_phr_file = os.path.join(target_path, 'ws', 'phr_occ.phr')
    fh_phr_occ_all = codecs.open(phr_occ_all_file, 'r', encoding='utf-8')
    fh_phr_occ_phr = codecs.open(phr_occ_phr_file, 'w', encoding='utf-8')

    # first collect all phrases
    print "Creating", phr_occ_phr_file 
    current_fname = None
    count = 0
    for line in fh_phr_occ_all:
        (fname, year, phrase, sentence) = line.strip("\n").split("\t")
        fname = fname.split('.xml_')[0] + '.xml'
        if fname != current_fname:
            current_fname = fname
            count += 1
        if count > limit:
            break
        fh_phr_occ_phr.write(phrase+"\n")

    # now create phr_occ.uct and phr_occ.unlab
    phr_occ_uct_file = os.path.join(target_path, 'ws', 'phr_occ.uct')
    phr_occ_unlab_file = os.path.join(target_path, 'ws', 'phr_occ.unlab')
    print "Creating", phr_occ_uct_file 
    command = "cat %s | sort | uniq -c | sort -nr | python reformat_uc.py > %s" \
              % (phr_occ_phr_file, phr_occ_uct_file)
    print '%', command
    subprocess.call(command, shell=True)    
    print "Creating", phr_occ_unlab_file 
    command = "cat %s | sed -e 's/^[0-9]*\t/\t/' > %s" \
              % (phr_occ_uct_file, phr_occ_unlab_file)
    print '%', command
    subprocess.call(command, shell=True)    

    
def run_annotate2(target_path, language, limit):

    """Prepare two files that can be used for evaluation. One file named
    phr_occ.eval.unlab that lists a term-file pairs from n=limit files where all contexts
    are listed following the pair. This file is input for manual annotation. And one file
    named doc_feats.eval which is a subset of doc_feats.all, but it contains only those
    term-file pairs that occur in phr_occ.eval.unlab."""
    
    eval1 = os.path.join(target_path, 'ws', 'phr_occ.eval.unlab')
    eval2 = os.path.join(target_path, 'ws', 'doc_feats.eval')
    eval3 = os.path.join(target_path, 'ws', 'phr_occ.eval.unlab.html')
    eval4 = os.path.join(target_path, 'ws', 'phr_occ.eval.unlab.txt')
    fh_eval1 = codecs.open(eval1, 'w', encoding='utf-8')
    fh_eval2 = codecs.open(eval2, 'w', encoding='utf-8')
    fh_eval3 = codecs.open(eval3, 'w', encoding='utf-8')
    fh_eval4 = codecs.open(eval4, 'w', encoding='utf-8')

    fh_eval3.write("<html>\n")
    fh_eval3.write("<head>\n")
    fh_eval3.write("<style>\n")
    fh_eval3.write("np { color: blue; }\n")
    fh_eval3.write("</style>\n")
    fh_eval3.write("</head>\n")
    fh_eval3.write("<body>\n")
    fh_eval4.write("# Terms to be annotated for evaluation, using first %d patents\n\n" % limit)

    phr_occ_array = _read_phr_occ(target_path, language, limit)
    doc_feats_array = _read_doc_feats(target_path, language, limit)

    # sort phrases on how many contexts we have for each
    phrases = phr_occ_array.keys()
    sort_fun = lambda x: sum([len(x) for x in phr_occ_array[x].values()])
    for phrase in reversed(sorted(phrases, key=sort_fun)):
        fh_eval3.write("<p>%s</p>\n" % phrase)
        fh_eval4.write("\t%s\n" % phrase)
        if not (phr_occ_array.has_key(phrase) and doc_feats_array.has_key(phrase)):
            continue
        for doc in phr_occ_array[phrase].keys():
            fh_eval1.write("\n?\t%s\t%s\n\n" % (phrase, doc))
            for sentence in phr_occ_array[phrase][doc]:
                fh_eval3.write("<blockquote>%s</blockquote>\n" % sentence)
                lines = textwrap.wrap(sentence, 100)
                fh_eval1.write("\t- %s\n" %  lines[0])
                for line in lines[1:]:
                    fh_eval1.write("\t  %s\n" % line)
        for doc in doc_feats_array[phrase].keys():
            for sentence in doc_feats_array[phrase][doc]:
                fh_eval2.write(sentence)

                
def _read_phr_occ(target_path, language, limit):
    """Return the contents of ws/phr_occ.all in a dictionary."""
    def get_stuff(line):
        """Returns the file name, the phrase and the context, here the context is the
        sentence listed with the phrase."""
        (fname, year, phrase, sentence) = line.strip("\n").split("\t")
        fname = fname.split('.xml_')[0]
        return (fname, phrase, sentence)
    return _read_phrocc_or_docfeats('phr_occ.all', get_stuff)

def _read_doc_feats(target_path, language, limit):
    """Return the contents of ws/doc_feats.all in a dictionary."""
    def get_stuff(line):
        """Returns the file name, the phrase and the context, here the context is the
        entire line."""
        (phrase, id, feats) = line.strip("\n").split("\t", 2)
        (year, fname, phrase2) = id.split('|', 2)
        return (fname, phrase, line)
    return _read_phrocc_or_docfeats('doc_feats.all', get_stuff)

def _read_phrocc_or_docfeats(fname, get_stuff_fun):
    phr_occ_file = os.path.join(target_path, 'ws', fname)
    fh_phr_occ = codecs.open(phr_occ_file, encoding='utf-8')
    phr_occ_array = {}
    current_fname = None
    count = 0
    for line in fh_phr_occ:
        fname, phrase, context = get_stuff_fun(line)
        if count >= limit:
            break
        if fname != current_fname:
            current_fname = fname
            count += 1
        phr_occ_array.setdefault(phrase, {})
        phr_occ_array[phrase].setdefault(fname, []).append(context)
    return phr_occ_array



if __name__ == '__main__':

    (opts, args) = getopt.getopt(
        sys.argv[1:],
        'l:s:t:n:r:',
        ['annotate1', 'annotate2', 'verbose'])

    annotate1, annotate2 = False, False
    verbose = False
    
    for opt, val in opts:

        if opt == '-l': language = val
        if opt == '-t': target_path = val
        if opt == '--annotate1': annotate1 = True
        if opt == '--annotate2': annotate2 = True
        if opt == '--verbose': verbose = True
        
    # Note: At this point, user must manually create an annotated file phr_occ.lab, it is
    # expected that this file lives in ../annotation/<language>. It is automatically
    # copied to the <language>/ws subdirectory in the next step.
        
    if annotate1:
        run_annotate1(target_path, language, limit)
    elif annotate2:
        run_annotate2(target_path, language, limit)
