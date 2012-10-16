"""

Main script for the technology tagger.

Usage:

    % python main.py [OPTIONS] -o OUTPUT_DIR FILE_LIST
    % python main.py [OPTIONS] --infile INPATH --outfile OUTPATH

    Use the first version to run in batch on the elements listed in FILE_LIST, writing
    results to OUTPUT_DIR. Results are either overview html files or individual fact
    files. In the latter case, the names of files written to OUTPUT_DIR are the
    concatenation of the the basename of the path in FILE_LIST and '.tech'.

    One of the options is to set the mode. In monolingual mode, fact files are created for
    each input file. In multilingual mode, html overview files are created for the entire
    file list and for each year.
    
    The second version can only be used for the monolingual mode (it implies --mode=MONO)
    and requires a path for the input file and the output file.
    
    OPTIONS
        
       [-l en|de|cn]          language, 'en' by default
       [--debug]              switches off error trapping
       [--cap N]              indicates limit to number of files processed
       [--mode MONO|MULTI]    sets monolingual or multilingual mode, MULTI by default
                                
"""


import os, sys, getopt, time, codecs, pprint, glob

#saved_dir = os.getcwd()
#os.chdir('..')
#sys.path.insert(0, os.getcwd())
#os.chdir(saved_dir)

script_path = os.path.abspath(sys.argv[0])
script_dir = os.path.dirname(script_path)
os.chdir(script_dir)
os.chdir('..')
sys.path.insert(0, os.getcwd())
os.chdir(script_dir)

import runtime.utils.test
from utils.docstructure.main import Parser
from utils.splitter import Splitter
from utils.tries.matcher import Matcher, Trie
from html import HTML_PREFIX, HTML_END

# trap as many Exceptions as possible, this default can be overruled here or from the
# command line
TRAP_ERRORS = True

# process all elements of the input list, positive integers indicate a limit to the number
# of files processed, this default can be overruled here or from the command line
CAP = 0


def usage():
    print "Usage: % python main.py [--debug] [--cap N] " + \
          "[-l LANGUAGE] [-o OUTPUT_DIR] FILE_LIST\n"


def handle_exception(e, message=None):
    message_string = "Exception occured." if message is None else message
    print "WARNING: %s" % message_string
    try:
        print e.__class__.__name__, e
    except Exception:
        pass

    
class TechnologyTagger(object):

    """
    Main class, reponsible for:
    - reading the list of files to process
    - running the Document Structure Parser
    - reading in the list of technologies (into a trie)
    - reading patterns (future functionailty)
    - looking up technologies in parts of the documents
    - using weights depending on location in document (future functionailty)
    - collecting and storing results
    - calculate maturity scores for each document
    - calling the Scorer to calculate year-by-year scores and RDG score
    - calling the Exporter to generate output
    """

    def __init__(self, language, output_dir, file_list, infile=None, outfile=None):
        self.language = language
        self.output_dir = output_dir
        self.file_list = file_list
        self.infile = infile
        self.outfile = outfile
        if file_list is None:
            self.files = [infile]
        else:
            self.files = [l.strip() for l in open(file_list).readlines()]
        # a simple list of technologies, or perhaps tuples with maturity scores added
        # (note that the maturity scores are time stamped)
        # these will be used for the prefix trie lookup
        self.technologies = OntologyReader().technologies(language)
        self.lookup = Lookup(self.language, self.technologies)
        self.storage = ResultStore(self.technologies)
        self.exporter = Exporter(language, self.technologies, output_dir, '../ontology')

    def __str__(self):
        if self.file_list is not None:
            source = self.file_list
        else:
            source = os.path.basename(self.infile)
        return "<TechnologyTagger on \"%s\" language=\"%s\">" % (source, self.language)

    def process_files(self):
        self.clear_tmp_files()
        count = 0
        for filename in self.files:
            t1 = time.time()
            size = os.stat(filename).st_size
            count += 1
            print "%04d Processing %s" % (count, os.path.basename(filename)),
            if TRAP_ERRORS:
                try:
                    self.process_file(filename)
                except Exception, e:
                    handle_exception(e)
            else:
                self.process_file(filename)
            t2 = time.time()
            elapsed_time_per_kb = ((t2-t1)/size)*1000
            print "(%.4fs/Kb)" % elapsed_time_per_kb
            if count == CAP:
                break
        Scorer().score(self.storage)
        #self.storage.pp()
        if self.export_html:
            self.exporter.export_html(self.storage)
        if self.export_fact:
            self.exporter.export_fact(self.files, self.output_dir,
                                      self.infile, self.outfile, self.storage)

    def process_file(self, filename):
        """Run the document structure parser, select the section we want to use, perform
        technology lookup on those sections,and store the results."""
        self.filename = filename
        data = self._get_data_from_document()
        year = data['DATE'][:4]
        filtered_data = self._select_data(data)
        lookup_results = self.lookup.search(filtered_data)
        self.storage.add(os.path.basename(filename), year, lookup_results)
    
    def clear_tmp_files(self):
        #files = glob.glob('data/tmp/*')
        files = glob.glob('%sdata/tmp/*' % script_dir)
	for f in files:
            os.remove(f)

    def _get_data_from_document(self):
        """Return a data structure with sections from the document, includes some meta
        data and all sections where we expect to find technologies. It casts a wide net,
        downstream code may select a subset."""
        docparser = Parser()
        docparser.collection = 'LEXISNEXIS'
        docparser.write_files = False
        docparser.language = self.language
        (text_file, tags_file, fact_file, sect_file) = self._set_output_files()
        docparser.process_xml_file(self.filename, text_file, tags_file, fact_file, sect_file)
        data = {}
        for s in docparser.factory.sections:
            # TODO: should we add all paragraphs, in order to help the splitter?
            if 'Meta-Date' in s.types:
                data['DATE'] = s.text
            elif 'Meta-Title' in s.types:
                data['TITLE'] = s.text
            elif 'Technical_Field' in s.types:
                data.setdefault('TECHNICAL_FIELD', []).append(s.text)
            elif 'Background_Art' in s.types:
                data.setdefault('BACKGROUND_ART', []).append(s.text)
            elif 'Abstract' in s.types:
                data.setdefault('ABSTRACTS', []).append(s.text)
            elif 'Examples' in s.types:
                data.setdefault('EXAMPLES', []).append(s.text)
            elif 'Summary' in s.types:
                data.setdefault('SUMMARY', []).append(s.text)
            elif 'claim' in s.types:
                data.setdefault('CLAIMS', []).append(s.text)
            elif 'Description' in s.types:
                if not data.has_key('DESCRIPTION') or len(s.text) > len(data['DESCRIPTION']):
                    data['DESCRIPTION'] = s.text
        return data
        
    def _set_output_files(self):
        extensions = ('txt', 'tags', 'fact', 'sect')
        basename = os.path.basename(self.filename)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        #return ["data/tmp/%s-%s.%s" % (timestamp, basename, ext) for ext in extensions]
        return ["%s/data/tmp/%s-%s.%s" % (script_dir, timestamp, basename, ext) for ext in extensions]

    def _select_data(self, data):
        """Barebones version. Should return a list of tuples with type and weight:
        ('ABSTRACT', '1.0', 'We describe a ...'). """
        abstract, description = [], []
        if data.has_key('ABSTRACTS'):
            abstract = [('ABSTRACT', 1.0, data['ABSTRACTS'][0])]
        if data.has_key('DESCRIPTION'):
            description = [('DESCRIPTION', 0.4, data['DESCRIPTION'])] 
        return abstract + description



class OntologyReader(object):

    def technologies(self, language):
        """Read the technologies as stored in the lists for the three languages."""
        technology_file1 = "%s/technologies/%s/phr_occ6_identifiers.tab" % (script_dir, language)
        technology_file2 = "%s/technologies/%s/phr_occ5_maturity.tab" % (script_dir, language)
        technologies = {}
        with codecs.open(technology_file1, encoding='utf-8') as fh:
            for line in fh:
                (term, id) = line.strip().split("\t")
                technologies[term] = [id]
        with codecs.open(technology_file2, encoding='utf-8') as fh:
            for line in fh:
                (term, maturity) = line.strip().split("\t")
                technologies[term].append(maturity.split())
        #for k,v in technologies.items(): print k,v
        return technologies
        
    
class Lookup(object):

    def __init__(self, language, technologies):
        self.language = language
        self.splitter = Splitter(language)
        self.matcher = Matcher(Trie([(t,'t') for t in technologies.keys()]))
            
    def search(self, sections):
        use_boundaries = False if self.language == 'cn' else True
        technologies_found = []
        for (sectype, weight, text) in sections:
            fragments = self.splitter.split(text)
            for fragment in fragments:
                self.matcher.lookup(fragment, use_boundaries=use_boundaries)
                for r in self.matcher.result:
                    technologies_found.append((sectype, weight, u''.join(r.found)))
        return technologies_found

    
class ResultStore(object):

    def __init__(self, technologies):
        # This needs the technologies list to retrieve the maturity score
        self.technologies = technologies
        self.data = {}
        self.weights = {}
        self.overall_score = None   # will be added by the Scorer

    def add(self, filename, year, results):
        """Adding results, indexing on year and filename."""
        self._ensure_year(year)
        self._ensure_filename(year, filename)
        for (sectype, weight, technology) in results:
            self._ensure_filename_technology(year, filename, technology)
            self.weights[sectype] = weight
            technology_infile = self.get_technology(year, filename, technology)
            technology_inyear = self.get_technology(year, None, technology)
            for tech in (technology_inyear, technology_infile):
                tech[sectype] = tech.setdefault(sectype,0) + 1
                
    def get_years(self):
        return self.data.keys()
    
    def get_filenames(self, year):
        return self.data[year]['FILES'].keys()

    def get_year_of_file(self, filename):
        for year in self.get_years():
            if self.data[year]['FILES'].has_key(filename):
                return year
        return None
        
    def get_file_scores(self, year):
        return [d['SCORE'] for d in self.data[year]['FILES'].values()]
        
    def get_all_file_scores(self):
        scores = []
        for year in self.data.keys():
            scores.extend([d['SCORE'] for d in self.data[year]['FILES'].values()])
        return scores

    def get_all_year_scores(self):
        scores = []
        for year in sorted(self.data.keys()): 
            if self.data[year]['TOTAL'].has_key('SCORE'):
                scores.append((year, self.data[year]['TOTAL']['SCORE']))
        return scores

    def get_weight(self, section):
        return self.weights.get(section, 0)

    def get_maturity_score(self, technology, year):
        """Return the maturity level of the technology for the given year. This should
        query the ontology, or the list derived from the ontology that is stored in
        TechnologyTagger.technologies. For now, we just make it up."""
        tipping_points = self.technologies[technology][1]
        if year < tipping_points[0]:
            return 0
        elif year < tipping_points[1]:
            return 1
        else:
            return 2

    def get_score(self, year, filename=None):
        if filename is None:
            return self.data[year]['TOTAL']['SCORE']
        else:
            return self.data[year]['FILES'][filename]['SCORE']
    
    def set_score(self, year, filename, score):
        if filename is None:
            self.data[year]['TOTAL']['SCORE'] = score
        else:
            self.data[year]['FILES'][filename]['SCORE'] = score

    def get_technology(self, year, filename, technology):
        if filename is None:
            return self.data[year]['TOTAL']['TECHNOLOGIES'][technology]
        else:
            return self.data[year]['FILES'][filename]['TECHNOLOGIES'][technology]

    def get_technologies(self, year, filename=None):
        if filename is None:
            return self.data[year]['TOTAL']['TECHNOLOGIES']
        else:
            try:
                return self.data[year]['FILES'][filename]['TECHNOLOGIES']
            except KeyError:
                return []
            
    def get_all_technologies(self):
        all_technologies = {}
        for year in self.data.keys():
            technologies = self.get_technologies(year)
            for technology, counts in technologies.items():
                all_technologies.setdefault(technology, {})
                for section, count in counts.items():
                    all_technologies[technology].setdefault(section, 0)
                    all_technologies[technology][section] += count
        return all_technologies
    
    def _ensure_year(self, year):
        self.data.setdefault(year, { 'FILES': {}, 'TOTAL': { 'TECHNOLOGIES': {}}})
        
    def _ensure_filename(self, year, filename):
        self.data[year]['FILES'].setdefault(filename, { 'TECHNOLOGIES': {} })
        
    def _ensure_filename_technology(self, year, filename, technology):
        self.data[year]['FILES'][filename]['TECHNOLOGIES'].setdefault(technology, {})
        self.data[year]['TOTAL']['TECHNOLOGIES'].setdefault(technology, {})

    def collect_tuples(self, year, filename=None):
        """Returns a list of tuples of the form <technology, maturity level, section,
        weight, count>"""
        if filename is None:
            dictionary = self.data[year]['TOTAL']['TECHNOLOGIES']
        else:
            dictionary = self.data[year]['FILES'][filename]['TECHNOLOGIES']
        tuples = []
        for technology, counts in dictionary.items():
            maturity_level = self.get_maturity_score(technology, year)
            for section, count in dictionary[technology].items():
                w = self.get_weight(section)
                tuples.append([technology, maturity_level, section, w, count])
        return tuples

        
    def pp(self):
        """For each year, print the file list and the counts for all technologies. Does
        not print the totals or the numbers for individual files, although those data are
        available."""
        print "\npprint.PrettyPrinter(indent=4).pprint(self.data)\n"
        pprint.PrettyPrinter(indent=4).pprint(self.data)
        print
        for k,v in self.weights.items():
            print v, '-', k
        for year in sorted(self.data.keys()):
            print "\n%s" % year
            # print all filename
            if 0:
                for filename in sorted(self.data[year]['FILES'].keys()):
                    print '  ', filename
            # print total for all files
            if self.data[year]['TOTAL'].has_key('SCORE'):
                print "   SCORE = %.4f" % self.data[year]['TOTAL']['SCORE']
            if 0:
                for technology in sorted(self.data[year]['TOTAL']['TECHNOLOGIES'].keys()):
                    print '  ', technology, self.data[year]['TOTAL']['TECHNOLOGIES'][technology]
            # print file scores
            if 1:
                for fname in sorted(self.data[year]['FILES'].keys()):
                    print "  ", fname
                    print "     SCORE = %.4f" % self.data[year]['FILES'][fname]['SCORE']
                    for t in sorted(self.data[year]['FILES'][fname]['TECHNOLOGIES'].keys()):
                        print "    ", t, self.data[year]['FILES'][fname]['TECHNOLOGIES'][t]
        print "\nAVERAGE MATURITY SCORE = %.2f" % self.overall_score

        
    def print_data(self, year, basename):
        print self.data[year]['FILES'].get(basename,{})

        
        
    
class Scorer(object):

    """ The scoring scheme for calculating the average maturity scores over a year from
    the individual technology scores proceeds as follows. Each technology is associated
    with one or more tuples of technology name T, maturity level ML for the year, section name
    S, section weight W_s and number of times the technology occurred in the section (N):

       <T, ML, S, Ws, N>

    For each technology, there can be as many tuples as there are section types. Now let
    TUPLES_y = [ TUPLE1 ... TUPLEn ] be the set of tuples for a year. The aggregate
    maturity level is

       SUM(TUPLEi with 1<=i<=n1) [TUPLEi.ML * TUPLEi.Ws * TUPLE.C ]

    That is, multiply the maturity level with the weight and the count, and sum it over
    the set of tuples. In short hand: SUM(ML.Ws.N). This is adjusted for the total count
    adjusted by weights: SUM(Ws.C). This is a number from 0 to 2, which we will map to a
    number between 0 and 1. So the full formula is:

       (SUM(ML.Ws.N) / SUM(Ws.N)) / 2

    This formual may need to be revised. For example, if technology Ti occurs a thousand
    times and technology Tj occurs once, then Ti will count a 1000 more towards the result
    than technology Tj. But in general it may be better to solve these cases by not
    extracting all technologies from a patent, but be sensitive to the ones mentioned in
    certain contexts. """
    
    def score(self, result_store):

        # these two variables are used to calculate the overall score for the RDG
        self.sum_maturity_x_weight_x_count = 0
        self.sum_weight_x_count = 0

        for year in result_store.get_years():
            tuples = result_store.collect_tuples(year)
            score = self.calculate_score(tuples)
            result_store.set_score(year, None, score)
            for filename in result_store.get_filenames(year):
                tuples = result_store.collect_tuples(year, filename)
                score = self.calculate_score(tuples)
                result_store.set_score(year, filename, score)

        try:
            total_average_maturity1 = self.sum_maturity_x_weight_x_count / self.sum_weight_x_count
            total_average_maturity2 = total_average_maturity1 / 2
        except ZeroDivisionError:
            total_average_maturity2 = 0.0
        result_store.overall_score = total_average_maturity2

        
    def calculate_score(self, tuples):
        sum_maturity_x_weight_x_count = sum([t[1]*t[3]*t[4] for t in tuples])
        sum_weight_x_count = sum([t[3]*t[4] for t in tuples])
        self.sum_maturity_x_weight_x_count += sum_maturity_x_weight_x_count
        self.sum_weight_x_count += sum_weight_x_count
        try:
            return (sum_maturity_x_weight_x_count / sum_weight_x_count) / 2
        except ZeroDivisionError:
            # TODO: track when this happens
            return 0.0
        
    
class Exporter(object):

    def __init__(self, language, technologies, html_dir, ontology_dir):
        self.language = language
        self.technologies = technologies
        self.html_dir = html_dir
        self.ontology_dir = ontology_dir
        
    def export_html(self, result_store):
        self.result_store = result_store
        self.export_rdg()
        for year in result_store.get_years():
            try:
                self.export_year(year)
            except Exception, e:
                handle_exception(e, "Exception while exporting year %s" % year)

    def export_rdg(self):
        fh = codecs.open(os.path.join(self.html_dir, "rdg.html"), 'w', encoding='utf-8')
        fh.write(HTML_PREFIX)
        fh.write("<h1>Technological Maturity Scores for the RDG</h1>\n")
        self.export_maturity_score(fh)
        self.export_year_scores(fh)
        self.export_histogram(fh)
        self.export_technologies(fh)
        fh.write(HTML_END)
        fh.close()

    def export_year(self, year):
        fh = codecs.open(os.path.join(self.html_dir, "%s.html" % year), 'w', encoding='utf-8')
        fh.write(HTML_PREFIX)
        fh.write("<h1>Technological Maturity Scores for %s</h1>\n" % year)
        self.export_maturity_score(fh, year)
        self.export_histogram(fh, year)
        self.export_technologies(fh, year=year)
        fh.write(HTML_END)
        fh.close()
        
    def export_maturity_score(self, fh, year=None):
        if year is not None:
            fh.write("<h3>Average maturity score for %s</h3>\n" % year)
        else:
            fh.write("<h3>Average maturity score for the RDG</h3>\n")
        fh.write("<blockquote>\n")
        fh.write("<table cellspacing=0 cellpadding=5 border=1>\n")
        fh.write("<tr>\n")
        fh.write("  <td>AVERAGE_MATURITY_SCORE\n")
        if year is not None:
            fh.write("    <td>%.4f\n" % self.result_store.get_score(year))
        else:
            fh.write("    <td>%.4f\n" % self.result_store.overall_score)
        fh.write("</table>\n")
        fh.write("</blockquote>\n\n")
        
    def export_year_scores(self, fh):
        scores = self.result_store.get_all_year_scores()
        fh.write("<h3>Scores for all years</h3>\n")
        fh.write("<blockquote>\n")
        fh.write("<table cellpadding=3 cellspacing=0 border=1>\n")
        fh.write("<tr>\n")
        for year, score in scores:
            fh.write("  <td><a href=%s.html>%s</a></td>\n" % (year, year))
        fh.write("<tr>\n")
        for year, score in scores:
            fh.write("  <td>%.2f</td>\n" % score)
        fh.write("</table>\n")
        fh.write("</blockquote>\n\n")

        
    def export_histogram(self, fh, year=None):

        if year is not None:
            scores = self.result_store.get_file_scores(year)
        else:
            scores = self.result_store.get_all_file_scores()
        bins = [0,0,0,0,0,0,0,0,0,0]
        names = ['0.0-0.1', '0.1-0.2', '0.2-0.3', '0.3-0.4', '0.4-0.5',
                 '0.5-0.6', '0.6-0.7', '0.7-0.8', '0.8-0.9', '0.9-1.0']
        for score in scores:
            if score == 1:
                bins[9] += 1
            else:
                bins[int(str(score)[2])] += 1
        maxval = sorted(bins)[-1]
        year_str = year if year is not None else "All"

        #fh.write("<h3>Histogram of Maturity Score Distribution over %s Patents </h3>\n" % year_str)
        fh.write("<h3>Maturity Score Distribution over %s Patents </h3>\n" % year_str)
        fh.write("<blockquote>\n")
        if 0:
            fh.write("<pre>\n")
            for i in range(9, -1, -1):
                bar_string = "%s | %s" % (names[i], '+' * bins[i])
                fh.write("%s\n" % bar_string)
            bottom_line = '-' * maxval
            fh.write("        +-%s" % bottom_line)
            fh.write("</pre>\n")
        if 1:
            fh.write("<table cellpadding=3 cellspacing=0 border=1>\n")
            fh.write("<tr>\n")
            for name in  names:
                fh.write("  <td>%s\n\n" % (name))
            fh.write("<tr>\n")
            for bin in  bins:
                fh.write("  <td align=right>%d\n" % (bin))
            fh.write("</table>\n")
        fh.write("</blockquote>\n")
        
        
    def export_technologies(self, fh, year=None):
        fh.write("<h3>Technologies referenced, with occurrence count, maturity score, ")
        fh.write("and links to the ontology</h3>\n")
        fh.write("<blockquote>\n")
        fh.write("<table cellspacing=0 cellpadding=3 border=1>\n")
        if year is not None:
            technologies = self.result_store.get_technologies(year)
        else:
            technologies = self.result_store.get_all_technologies()
        # this can be used to reduce the number of technologies printed
        MIN_FREQUENCY = 1
        for t in sorted(technologies.keys()):
            technology_id = self.technologies[t][0]
            #print technologies[t]
            frequency = sum(technologies[t].values())
            #print type(frequency), frequency
            if frequency < MIN_FREQUENCY:
                continue
            fh.write("<tr>\n")
            fh.write("   <td><a href=ontology/t%s/index.html>%s</a>\n" % (technology_id, t))
            fh.write("   <td align=right>%d\n" % sum(technologies[t].values()))
            tipping_points = self.technologies[t][1]
            fh.write("   <td>%s\n" % tipping_points[0])
            fh.write("   <td>%s\n" % tipping_points[1])
            if year is not None:
                maturity_score = 0
                if int(year) >= int(tipping_points[0]):
                    maturity_score = 1
                if int(year) >= int(tipping_points[1]):
                    maturity_score = 2
                fh.write("   <td>%d\n" % maturity_score)
        fh.write("</table>\n")
        fh.write("</blockquote>\n")
        fh.write("\n")
        fh.write("\n")
        fh.write("\n")
        fh.write("\n")

        
    def export_fact(self, infiles, output_dir, infile, outfile, storage):
        #storage.pp()
        if infile and outfile:
            self.export_fact_for_file(infile, outfile, storage)
        else:
            for infile in infiles[:CAP]:
                outfile = os.path.join(output_dir, os.path.basename(infile) + '.tech')
                self.export_fact_for_file(infile, outfile, storage)

    def export_fact_for_file_et(self, infile, outfile, storage):
        if TRAP_ERRORS:
            try:
                self.export_fact_for_file_et(infile, outfile, storage)
            except:
                print "WARNING: error exporting data to", outfile
        else:
            self.export_fact_for_file_et(infile, outfile, storage)

    def export_fact_for_file(self, infile, outfile, storage):
        basename = os.path.basename(infile)
        year = storage.get_years()[0]
        year = storage.get_year_of_file(basename)
        technologies = storage.get_technologies(year, filename=basename)
        #storage.print_data(year, basename)
        fh = codecs.open(outfile, 'w', encoding='utf-8')
        if technologies:
            file_score = storage.data[year]['FILES'][basename]['SCORE']
            fh.write("AVERAGE_MATURITY_SCORE value=%.2f\n" % file_score)
            for t in technologies:
                freq = sum(technologies[t].values())
                score = storage.get_maturity_score(t, year)
                fh.write("TECHNOLOGY name=\"%s\" frequency=%s maturity_level=%d\n" % (t, freq, score))
        fh.close()

        
def run(language, output_dir, file_list, infile, outfile, mode):

    if output_dir and file_list:
        tagger = TechnologyTagger(language, output_dir, file_list)
        if mode == 'MONO':
            tagger.export_fact = True
            tagger.export_html = False
        else:
            tagger.export_fact = False
            tagger.export_html = True
        tagger.process_files()
        # tagger.process_file("data/US4192770A.xml")
        # tagger.process_file("data/DE3539484C1.xml")
        # tagger.process_file("data/CN101243817A.

    elif infile and outfile:
        tagger = TechnologyTagger(language, None, None, infile=infile, outfile=outfile)
        tagger.export_fact = True
        tagger.export_html = False
        # when called from here, this will only process one file
        tagger.process_files()
        
    else:
        print "WARNING: nothing to do"


        
if __name__ == '__main__':

    try:
        (opts, args) = getopt.getopt(sys.argv[1:],
                                     'l:o:',
                                     ['debug', 'cap=', 'infile=', 'outfile=', 'mode='])
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2)

    language = 'en'
    mode = 'MULTI'
    output_dir = None
    file_list = None
    infile = None
    outfile = None

    for opt, val in opts:
        if opt == '-l': language = val
        elif opt == '--mode': mode = val
        elif opt == '-o': output_dir = val
        elif opt == '--debug': TRAP_ERRORS = False
        elif opt == '--cap': CAP = int(val)
        elif opt == '--infile': infile = val
        elif opt == '--outfile': outfile = val
    if args:
        file_list = args[0]

    if TRAP_ERRORS:
        try:
            run(language, output_dir, file_list, infile, outfile, mode)
        except Exception, e:
            handle_exception(e)
    else:
        run(language, output_dir, file_list, infile, outfile, mode)
