import os, sys, getopt, codecs

sys.path.append(os.path.abspath('../..'))
from ontology.utils.git import get_git_commit



def create_usage_file(corpus, matches, tscores, output, verbose):
    matches = os.path.join(corpus, 'data', 'o2_matches', matches, 'match.results.summ.txt')
    tscores = os.path.join(tscores, 'classify.MaxEnt.out.s4.scores.sum.az')
    out = codecs.open(output, 'w', encoding='utf-8')
    write_info(out, corpus, matches, tscores)

def write_info(out, corpus, matches, tscores):
    out.write("$ python %s\n\n" % ' '.join(sys.argv))
    out.write("git_commit = %s\n\n" % get_git_commit())
    out.write("corpus  = %s\n" % corpus)
    out.write("matches = %s\n" % matches)
    out.write("tscores = %s\n" % tscores)



def check_args(corpus, matches, tscores, output):
    if corpus is None:
        exit("ERROR: no corpus specified with --corpus option")
    elif matches is None:
        exit("ERROR: no matches file specified with --matches option")
    elif tscores is None:
        exit("ERROR: no technology scores file specified with --tscores option")
    elif output is None:
        exit("ERROR: no output file specified with --output option")


        

if __name__ == '__main__':
    
    options = ['output=', 'corpus=', 'matches=', 'techscores=', 'verbose']
    (opts, args) = getopt.getopt(sys.argv[1:], 'o:c:m:t:v', options)
    
    output = None
    corpus = None
    matches = None
    tscores = None
    verbose = False
    
    for opt, val in opts:
        if opt in ('--output', '-o'): output = val
        elif opt in ('--corpus', '-c'): corpus = val
        elif opt in ('--matches', '-m'): matches = val
        elif opt in ('--tscores', '-t'): tscores = val
        elif opt in ('--verbose', '-v'): verbose = True

    check_args(corpus, matches, tscores, output)
    create_usage_file(corpus, matches, tscores, output, verbose)
