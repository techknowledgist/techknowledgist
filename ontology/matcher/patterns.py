"""

Need to run this scirpt from this directory. (NO, not true anymore)

"""


import re, os, sys, codecs, string, getopt

script_path = os.path.abspath(sys.argv[0])
script_dir = os.path.dirname(script_path)
os.chdir(script_dir)
os.chdir('..')
os.chdir('..')
sys.path.insert(0, os.getcwd())
os.chdir(script_dir)

from ontology.utils.batch import read_stages, update_stages, write_stages


def read_patterns(input_file):
    """Read patterns from a file, create a list of patterns"""
    f = codecs.open(input_file, encoding = 'utf8')
    pattern_list = []
    pattern = f.readline()
    while pattern:
        pattern_list.append(pattern.split()) 
        pattern = f.readline()
    return pattern_list


def find_technologies(patterns, input_file, output_file, limit=0):

    """Find pattern matches in a file and output results in the format:
    <document_ID>\t<document_year>\t<PatternID>\t<Pattern_part1>\t<Patter_part2>\t<technology_name>."""

    f1 = codecs.open(input_file, encoding = 'utf8')
    f2 = codecs.open(output_file, 'w', encoding = 'utf8')
    #phrase = f1.readline()
    #while phrase:
    for phrase in f1
        for p in patterns:
            count = 0
            matched_part = ''
            for part in p[1:]:
                match = re.findall(part, phrase)
                if len(match) > 0:
                    matched_part += match[0] + '\t'
                if len(match) > 0:
                    count += 1
            # if all parts of the pattern matched the line
            if count == len(p) - 1: 
                # Find the name of the technology in the input line
                word = ''
                for w in phrase.split()[1:len(phrase.split())]:
                    if (word == '') and ('=' in w):
                        ind = phrase.split().index(w)
                        word += string.join(phrase.split()[2:ind], ' ')
                f2.write(phrase.split()[0] + '\t' + phrase.split()[1] + '\t' +
                matched_part + re.sub('_', ' ', word) + '\n')
        #phrase = f1.readline()



if __name__ == '__main__':

    target_path = os.path.join('..', 'creation', 'data', 'patents')
    language = 'en'
    limit = 0

    (opts, args) = getopt.getopt(sys.argv[1:], 'l:t:n:', [])
    for opt, val in opts:
        if opt == '-l': language = val
        if opt == '-t': target_path = val
        if opt == '-n': limit = int(val)

    patterns_file = "./patterns_%s.txt" % language
    features_file = os.path.join(target_path, language, "ws", "phr_feats.all")
    matches_file = os.path.join(target_path, language, "ws", "matches.all")

    patterns = read_patterns(patterns_file)
    find_technologies(patterns, features_file, matches_file)
