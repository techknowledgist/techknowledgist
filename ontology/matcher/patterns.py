

import re
import os
import codecs

"""Read patterns from a file, create a list of patters"""

def read_patterns(input_file):
    f = open(input_file, 'r')
    pattern_list = []
    pattern = f.readline()
    while pattern:
        pattern_list.append([pattern.split()[0], pattern.split()[1], pattern.split()[2]]) 
        pattern = f.readline()

    return pattern_list


"""Find pattern matches in a file and output results
in the format:
<document_ID>\t<document_year>\t<PatternID>\t<Pattern_part1>\t<Patter_part2>\t<technology_name>.
Return a list of found technologies."""

def find_technologies(patterns, input_file, output_file):
    tecs = []
    f1 = open(input_file, 'r')
    phrases = []
    phrase = f1.readline()
    while phrase:
        phrases.append(phrase)
        phrase = f1.readline()

    f2 = open(output_file, 'w')
    for phrase in phrases:
        for p in patterns:
            match1 = re.findall(p[1], phrase)
            match2 = re.findall(p[2], phrase)
            if len(match1) > 0 and len(match2) > 0:

                #Find the name of the technology in the input file
                word = ''
                for w in phrase.split()[1:len(phrase.split())]:
                    if (word == '') and ('=' in w):
                        ind = phrase.split().index(w)
                        word += phrase.split()[ind - 1]
       
                f2.write(phrase.split()[0] + '\t' + phrase.split()[1] + '\t' +
                str(p[0]) + '\t' + str(p[1]) + '\t' + str(p[2]) + '\t' +
                re.sub('_', ' ', word) + '\n')
                
                tecs.append(phrase.split('\t')[0])

    tecs = set(tecs)
    return tecs



if __name__ == '__main__':

    patterns = read_patterns('./patterns.txt')            
    find_technologies(patterns, "./phr_feats.all", "./matches.txt")       

