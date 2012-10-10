"""

Simple matcher, used as a stand in for Olga's code.

Given a language and a base directory form config.py, it takes files from
base_dir/language/phr_occ and creates a file base_dir/language/phr_occ2.tab, which has
lines like

   US4192770A.xml_78       7
   US4192770A.xml_649      7
   US4199325A.xml_71       3

This indcates that the pattern with id=7 matched the lines identified by US4192770A.xml_78
and US4192770A.xml_649 and that the pattern with id=7 matched the line identified by
US4199325A.xml_71.

Usage:

   % python matcher.py [-l LANGUAGE]

Patterns themselves are defined in patterns.py. Which now only works for English, need to
load German and Chinese patterns from files.

"""


import glob, os, sys, codecs

from config import BASE_DIR
from patterns import patterns
from utils import read_opts


LANGUAGE = 'en'
                                

def usage():
    print "Usage:"
    print "% python matcher.py [-l LANGUAGE]"


def match(source_dir, phr_occ2_file, patterns):
    
    out = codecs.open(phr_occ2_file, 'w')
    
    subdirs = glob.glob(os.path.join(source_dir, "*"))
    for subdir in subdirs:
        print subdir
        year = os.path.basename(subdir)
        files = glob.glob(os.path.join(subdir, "*.xml"))
        for fname in files:
            infile = codecs.open(fname)
            for line in infile:
                # TODO: must do somehting about lines with extra square brackets
                try:
                    (match_id, year, term, sentence) = line.strip().split("\t")
                    (left_context, rest) = sentence.split("[")
                    (t, right_context) = rest.split("]")
                    tokens_left = left_context.strip().split()[-3:]
                    tokens_right = right_context.strip().split()[:3]
                    for (pattern_id, pattern) in patterns.items():
                        side, regexp, name = pattern
                        context = tokens_right if side == 'r' else tokens_left
                        result = find_match(regexp, context)  
                        if result:
                            out.write("%s\t%s\n" % (match_id, pattern_id))
                except ValueError:
                    print "WARNING: error in line:", line


def find_match(regexp, context):
    for token in context:
        result = regexp.search(token)
        if result is not None:
            return True
    return False


                        
if __name__ == '__main__':

    language = LANGUAGE
    (opts, args) = read_opts('l:', [], usage)
    for opt, val in opts:
        if opt == '-l': language = val

    patterns = patterns(language)
    source_dir = os.path.join(BASE_DIR, language, 'phr_occ')
    phr_occ2_file = os.path.join(BASE_DIR, language, 'selector', 'phr_occ2_matcher.tab')
    
    match(source_dir, phr_occ2_file, patterns)

    

