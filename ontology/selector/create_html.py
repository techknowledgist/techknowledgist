"""

Creates the HTML version of the ontology.

Input:
   - BASE_DIR/language/idx/index
   - BASE_DIR/language/idx/index.sizes.txt
   - BASE_DIR/language/selector/phr_occ4_selector.tab
   - BASE_DIR/language/selector/phr_occ5_maturity.tab

"""

import glob, os, sys, codecs, subprocess

from config import BASE_DIR
from patterns import patterns
from utils import read_opts, read_frequencies
from utils import html_prefix, html_end, html_explain, write_histogram

LANGUAGE = 'en'


def usage():
    print "Usage:"
    print "% python create_html.py [-l LANGUAGE] HTML_DIR"



class Ontology(object):

    def __init__(self, frequencies, maturity_scores, patterns):
        self.data = {}
        self.frequencies = frequencies
        self.maturity_scores= maturity_scores
        self.patterns = patterns
        
    def add(self, match_id, year, term, sentence, patterns):
        if not self.data.has_key(term):
            freqs = self.frequencies.get(term,{})
            if not freqs:
                print "WARNING: no frequencies found for '%s'" % term
            score = self.maturity_scores.get(term, False)
            if not score:
                print "WARNING: no maturity scores found for '%s'" % term
                score = (9999, 9999)
            self.data[term] = { 'matches': { 'ALL': {} },
                                'frequencies': freqs,
                                'maturity_score': score }
        self.data[term]['matches']['ALL'].setdefault(year,[])
        self.data[term]['matches']['ALL'][year].append((match_id,sentence, patterns))
        for pattern in patterns:
            self.data[term]['matches'].setdefault(pattern,{})
            self.data[term]['matches'][pattern].setdefault(year,[])
            self.data[term]['matches'][pattern][year].append((match_id,sentence, patterns))

    def get_terms(self):
        return sorted(self.data.keys())

    def get_term_id(self, term):
        return self.data[term]['id']
        
    def get_all_matches(self, term):
        return self.data[term]['matches']['ALL']

    def get_pattern_matches(self, term, pattern):
        return self.data[term]['matches'][pattern]

    def get_matching_patterns(self, term):
        return [ p for p in self.data[term]['matches'].keys() if p != 'ALL']

    def get_tipping_point(self, term):
        return self.data[term]['maturity_score'][1]
        
    def set_term_identifiers(self):
        term_id = 0
        for term in self.data.keys():
            term_id += 1
            self.data[term]['id'] = "%05d" % term_id

    def export_term_identifiers(self, fname):
        fh = codecs.open(fname, 'w')
        for term in self.data.keys():
            fh.write("%s\t%s\n" % (term, self.data[term]['id']))
            
    def export_as_html(self, html_directory):
        fh_index = codecs.open(os.path.join(html_directory, 'index.html'), 'w')
        fh_index.write(html_prefix)
        fh_index.write("<ol>\n")
        for term in self.get_terms():
            term_id = self.get_term_id(term)
            dir = os.path.join(html_directory, "t" + term_id)
            if not os.path.exists(dir):
                os.mkdir(dir)
            fh_index.write("<li><a href=t%s/index.html>%s</a></li>\n" % (term_id, term))
            self.export_term_as_html(dir, term, term_id)
            self.export_term_matches_as_html(dir, term, term_id)
        fh_index.write("</ol>\n")
        fh_index.write(html_end)
        fh_explain = codecs.open(os.path.join(html_directory, 'explain_figure.html'), 'w')
        fh_explain.write(html_explain)
        
    def export_term_as_html(self, html_directory, term, term_id):
        fh = codecs.open(os.path.join(html_directory, 'index.html'), 'w')
        fh.write(html_prefix)
        fh.write("<h2>%s</h2>" % term)
        fh.write("<p>Total number of mentions: %d</p>" % \
                      sum(self.frequencies.get(term,0).values()))
        fh.write("<p>Technology became widely available in %s<p>" % self.get_tipping_point(term))
        fh.write("<p>Distribution per year of term mentions in reference data " + \
                 "(<a href=../explain_figure.html>explain figure</a>)</p>\n")
        fh.write("<blockquote>\n")
        fh.write("<pre>\n")
        write_histogram(fh, term, self.frequencies[term])
        fh.write("</pre>\n")
        fh.write("<p>Note: the height of the vertical bar for a year reflects " + \
                      "the percentage of all term mentions in that year relative " + \
                      "to the total</p>\n")
        fh.write("</blockquote>\n\n")
        fh.write("<p>The term in context (capped at 5 matches per year, click " + \
                 "<a href=all.html>here</a> to see a full list) </p>\n")
        fh.write("<blockquote>\n")
        all_matches = self.get_all_matches(term)
        write_matches(fh, all_matches, "", term, table=True, cap=5, embed=True)
        fh.write("</blockquote>\n")
        fh.write("")
        fh.write("")
        fh.write(html_end)

    def export_term_matches_as_html(self, html_directory, term, term_id):
        all_matches = self.get_all_matches(term)
        patterns = self.get_matching_patterns(term)
        fh_all = codecs.open(os.path.join(html_directory, 'all.html'), 'w')
        write_matches(fh_all, all_matches, "All matches for %s" % term, term, table=False, cap=1000)
        
        
    def pp(self):
        for term in sorted(self.data.keys()):
            print self.data[term]['id'], term
            print ' ', self.data[term]['maturity_score']
            all_matches = self.get_all_matches(term)
            print "  ALL",
            for year in sorted(all_matches.keys()):
                print "%s:%s" % (year, len(all_matches[year])),
            print
            patterns = self.get_matching_patterns(term)
            if patterns:
                for pattern in sorted(patterns):
                    matches = self.get_pattern_matches(term ,pattern)
                    for year in sorted(matches.keys()):
                        print "  p%s %s:%s" % (pattern, year, len(matches[year]))
            print

        
def create_html(index_file, patterns, phr_occ4_file, phr_occ5_file, phr_occ6_file,
                language, html_directory):

    maturity_scores = load_maturity_scores(phr_occ5_file)
    #frequencies = shelve.open(index_file)
    frequencies = read_frequencies(os.path.dirname(index_file))
    infile = codecs.open(phr_occ4_file)

    ontology = Ontology(frequencies, maturity_scores, patterns)
    
    for line in infile:
        (match_id, year, term, sentence, patterns) = line.strip().split("\t")
        patterns = patterns.strip("[]")
        ontology.add(match_id, year, term, sentence, patterns)

    ontology.set_term_identifiers()
    ontology.export_term_identifiers(phr_occ6_file)
    ontology.export_as_html(html_directory)
    #ontology.pp()

    
def load_maturity_scores(phr_occ5_file):
    scores = {}
    for line in codecs.open(phr_occ5_file):
        (term, maturity) = line.strip().split("\t")
        scores[term] = maturity.split()
    return scores


def write_matches(fh, dict, h2_string, term, table=True, cap=10, embed=False):
    if not embed:
        fh.write(html_prefix)
        fh.write("<h2>%s</h2>\n" % h2_string)
    if table:
        fh.write("<table cellspacing=0 cellpadding=3 border=1>\n")
    for year in sorted(dict.keys()):
        if table:
            fh.write("<tr><td valign=top>%s\n" % year)
            fh.write("<td>\n")
        else:
            fh.write("<p>%s</p>\n" % year)
            fh.write("<blockquote>\n")
        for match in dict[year][:cap]:
            sentence = match[1]
            fh.write("<p>%s</p>\n" % (sentence))
        if table:
            fh.write("</tr>\n")
        else:
            fh.write("</blockquote>\n")
    if not embed:
        fh.write(html_end)
            

        
if __name__ == '__main__':

    language = LANGUAGE
    (opts, args) = read_opts('l:', [], usage)
    for opt, val in opts:
        if opt == '-l': language = val

    patterns = patterns(language)
    index_file = os.path.join(BASE_DIR, language, 'idx', 'index')
    phr_occ4_file = os.path.join(BASE_DIR, language, 'selector', 'phr_occ4_selector.tab')
    phr_occ5_file = os.path.join(BASE_DIR, language, 'selector', 'phr_occ5_maturity.tab')
    phr_occ6_file = os.path.join(BASE_DIR, language, 'selector', 'phr_occ6_identifiers.tab')
    directory = args[0]
    
    create_html(index_file, patterns, phr_occ4_file, phr_occ5_file, phr_occ6_file, language, directory)
