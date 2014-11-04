"""

Script to analyze the time series in files with maturity scores (which are
available from 1997-2007)..

Usage:

    $ python analyze_maturity_scores.py --trends 2000 2007
    $ python analyze_maturity_scores.py --distribution
    $ python analyze_maturity_scores.py --classify

The first invocation picks out the terms that had been trending up between the
two years. Trending means that socre(year1) > 0 and score(year2) > 0.1 and
score(year2) > 3 * score(year1).

The second invocation prints the counts for scores in particular ranges. There
are elevens ranges: score = 0, 0 < score <= 0.1, 0.1 < score < 0.2, etcetera.

"""

import os, sys, codecs

# path to the corpus directory
CORPUS_DIR = '/home/j/corpuswork/fuse/FUSEData/corpora/ln-us-all-600k'

# name of the time series directory in the corpus directory
TIME_SERIES = 'time-series-v2/maturity-scores'




class Scores(object):

    def __init__(self, scores_file):
        self.source = scores_file
        self.index = {}
        self.terms = {}
        fh = codecs.open(scores_file, encoding='utf8')
        maxcount = 10000
#        maxcount = sys.maxint
        years = fh.readline().split()[:-1]
        for i in range(len(years)):
            #print i, years[i]
            self.index[years[i]] = i
        count = 0
        for line in fh:
            count += 1
            if count > maxcount: break
            fields = line.rstrip().split("\t")
            term = fields.pop()
            if len(fields) == 11:
                self.terms[term.strip()] = [float(f) for f in fields]

    def get_scores(self, term):
        return self.terms.get(term)

    def get_score(self, term, year):
        scores = self.get_scores(term)
        if scores is None:
            return None
        return scores[self.index[year]]

    def get_trend(self, y1, y2):
        fh = codecs.open("trends-%s-%s.txt" % (y1, y2), 'w', encoding='utf8')
        for term in self.terms.keys():
            s1 = self.get_score(term, y1)
            s2 = self.get_score(term, y2)
            if s1 > 0 and s2 > 0.1 and s2 > (3 * s1):
                fh.write("%.4f\t%.4f\t%.4f\t%s\n" % (s1, s2, s2 - s1, term))

    def get_distribution(self):
        self.bin_names = ['0.0', '0.1', '0.2', '0.3', '0.4', '0.5',
                          '0.6', '0.7', '0.8', '0.9', '1.0']
        self.bins = dict.fromkeys(self.bin_names, 0)
        for scores in self.terms.values():
            for score in scores:
                if score == 0: self.bins['0.0'] += 1
                elif score <= 0.1: self.bins['0.1'] += 1
                elif score <= 0.2: self.bins['0.2'] += 1
                elif score <= 0.3: self.bins['0.3'] += 1
                elif score <= 0.4: self.bins['0.4'] += 1
                elif score <= 0.5: self.bins['0.5'] += 1
                elif score <= 0.6: self.bins['0.6'] += 1
                elif score <= 0.7: self.bins['0.7'] += 1
                elif score <= 0.8: self.bins['0.8'] += 1
                elif score <= 0.9: self.bins['0.9'] += 1
                elif score <= 1.0: self.bins['1.0'] += 1
                else:
                    print score
        self.print_bins()

    def get_classification(self):
        #fh = codecs.open('tscores.txt', 'w', encoding='utf8')
        growing = []
        growing_from_zero = []
        growing_from_zero_to_two = []
        for term, scores in self.terms.items():
            tscores = [get_ternary_score(s) for s in scores]
            #fh.write("%s %s\n" % (' '.join(["%s" % t for t in tscores]), term))
            #print "%s %s" (' '.join(["%s" % t for t in tscores]), term)
            if shows_growth(scores):
                growing.append([term, scores])
            if shows_growth_from_zero(scores):
                print tscores, term
                print scores
                growing_from_zero.append([term, scores])
            if shows_growth_from_zero_to_two(tscores):
                growing_from_zero_to_two.append([term, scores])
        print len(growing), 'growing'
        print len(growing_from_zero), 'growing_from_zero'
        print len(growing_from_zero_to_two), 'growing_from_zero_to_two'
        fh = codecs.open('tscores-growing-from-zero.txt', 'w', encoding='utf8')
        for term, scores in growing_from_zero:
            fh.write("%s\t%s\n" % ("\t".join(["%.2f" % t for t in scores]), term))
        
    def print_bins(self):
        for n in self.bin_names:
            print n, self.bins[n]
        
    def test(self):
        print s.get_scores('a')
        print s.get_score('a', '2000')


def get_ternary_score(float):
    if float < 0.5: return 0
    elif float < 2: return 1
    else: return 2


def shows_growth(scores):
    if scores[-1] > (2 * scores[0]):
        return True
    return False

def shows_growth_from_zero(scores):
    if scores[0] < 0.5 and shows_growth(scores):
        return True
    return False

def Xshows_growth(tscores):
    if tscores[-1] > (222 * tscores[0]):
        return True
    return False

def Xshows_growth_from_zero(tscores):
    if tscores[0] == 0 and shows_growth(tscores):
        return True
    return False

def shows_growth_from_zero_to_two(tscores):
    if tscores[0] == 0 and tscores[-1] == 2:
        return True
    return False

    
if __name__ == '__main__':

    s = Scores(os.path.join(CORPUS_DIR, TIME_SERIES, "maturity-match-based.txt"))
    #s.test()

    if sys.argv[1] == '--trends':
        start_year = sys.argv[2]
        end_year = sys.argv[3]
        s.get_trend(start_year, end_year)

    if sys.argv[1] == '--distribution':
        s.get_distribution()

    if sys.argv[1] == '--classify':
        s.get_classification()
