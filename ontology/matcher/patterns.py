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


def find_technologies(patterns, input_file, output_file):
    """Find pattern matches in a file and output results in a tab separated file with
    fields document_ID, document_year, PatternID, technology_name, Pattern_part1,
    Patter_part2, ..."""
    f1 = codecs.open(input_file, encoding = 'utf8')
    f2 = codecs.open(output_file, 'w', encoding = 'utf8')
    for phrase in f1:
        (fname_id, year, term, rest) = phrase.strip("\n").split("\t", 3)
        for p in patterns:
            matched_part = pattern_matched(p, phrase)
            if not matched_part is False:
                line = "%s\t%s\t%s\t%s\t%s\n" % (fname_id, year, p[0], term, matched_part)
                f2.write(line)

                
def find_technologies_batch(patterns, target_path, language, limit, verbose):

    """Similar to find_technologies() in that it finds pattern matches in a file and
    output results in a tab separated file. The difference is that this version runs in
    batch mode and will only do those parts of the file that fall within the limit."""

    features_file = os.path.join(target_path, language, "ws", "phr_feats.all")
    matches_file = os.path.join(target_path, language, "ws", "matches.all")
    f1 = codecs.open(features_file, encoding = 'utf8')
    f2 = codecs.open(matches_file, 'a', encoding = 'utf8')

    stages = read_stages(target_path, language)
    begin = stages.get('--matcher', 0)
    end = begin + limit
    
    current_fname = None
    file_count = 0
    for phrase in f1:
        if file_count > end:
            break
        (fname_id, year, term, rest) = phrase.strip("\n").split("\t", 3)
        (current_fname, file_count) = update_state(fname_id, current_fname,
                                                   file_count, begin, end, verbose)
        if file_count > begin:
            for p in patterns:
                matched_part = pattern_matched(p, phrase)
                if not matched_part is False:
                    line = "%s\t%s\t%s\t%s\t%s\n" % (fname_id, year, p[0], term, matched_part)
                    f2.write(line)

    update_stages(target_path, language, '--matcher', limit)
        

def update_state(fname_id, current_fname, file_count, begin, end, verbose):
    """Update current file name and file count given the fname_id, which is an identifier
    that consists of a file name and an integer."""
    fname = fname_id.split('_')[0]
    if fname != current_fname:
        if verbose:
            bool = '+' if begin <= file_count < end else '-'
            print "\n%s %s" % (bool, fname),
        file_count += 1
        current_fname = fname
    return (current_fname, file_count)


def pattern_matched(p, phrase):
    """See whether pattern p matches the phrase, if yes, return the matched part, if no,
    return False."""
    count = 0
    matched_parts = []
    for part in p[1:]:
        match = re.findall(part, phrase)
        if len(match) > 0:
            matched_parts.append(match[0])
            count += 1
    # return the matched part if all parts of the pattern matched the line
    return "\t".join(matched_parts) if count == len(p) - 1 else False
                

if __name__ == '__main__':

    target_path = os.path.join('..', 'creation', 'data', 'patents')
    language = 'en'
    limit = 0
    verbose = False
    
    (opts, args) = getopt.getopt(sys.argv[1:], 'l:t:n:v', [])
    for opt, val in opts:
        if opt == '-l': language = val
        if opt == '-t': target_path = val
        if opt == '-n': limit = int(val)
        if opt == '-v': verbose = True

    patterns_file = "./patterns_%s.txt" % language
    patterns = read_patterns(patterns_file)

    #features_file = os.path.join(target_path, language, "ws", "phr_feats.all")
    #matches_file = os.path.join(target_path, language, "ws", "matches.all")
    #find_technologies(patterns, features_file, matches_file)

    find_technologies_batch(patterns, target_path, language, limit, verbose)
