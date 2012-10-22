"""

Print some statistics on maturity levels and maturity scores on the tech files in data/out.

"""


import glob, codecs

all_scores = []
non_zero_scores = []
maturity_scores = {'0':0, '1':0, '2':0}

def collect_counts():
    for fname in glob.glob("data/out/*tech"):
        for line in codecs.open(fname):
            if line.startswith('AVERAGE_MAT'):
                score = float(line[-5:])
                all_scores.append(score)
                if score > 0:
                    non_zero_scores.append(score)
            if line.startswith('TECHNOLOGY'):
                score = line[-2:-1]
                maturity_scores[score] += 1

def print_level_statistics():
    print "\nMATURITY LEVELS\n"
    total = sum(maturity_scores.values())
    total_1 = float(maturity_scores['1'])
    total_2 = float(maturity_scores['2'] * 2)
    #print total, total_1, total_2
    print "  N =", total
    print "  AVERAGE =", (total_1 + total_2) / total
    print "\n  DISTRIBUTION:"
    print "     0  %3d" % maturity_scores['0']
    print "     1  %3d" % maturity_scores['1']
    print "     2  %3d" % maturity_scores['2']

def print_score_statistics(name, scores):
    print "\n%s\n" % name
    print '  N =', len(scores)
    print '  AVERAGE =', sum(scores)/len(scores)
    bins = [0,0,0,0,0,0,0,0,0,0]
    names = ['0.0-0.1', '0.1-0.2', '0.2-0.3', '0.3-0.4', '0.4-0.5',
             '0.5-0.6', '0.6-0.7', '0.7-0.8', '0.8-0.9', '0.9-1.0']
    for score in scores:
        if score == 1:
            bins[9] += 1
        else:
            bins[int(str(score)[2])] += 1
    print "\n  DISTRIBUTION:"
    for i in range(len(bins)):
        print "    %s  %4d" % (names[i], bins[i])


if __name__ == '__main__':

    collect_counts()
    #print 'MATURITY_SCORES', maturity_scores
    print_level_statistics()
    print_score_statistics('ALL SCORES', all_scores)
    print_score_statistics('NON ZERO SCORES', non_zero_scores)
    
