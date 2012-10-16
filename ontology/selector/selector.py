import glob, os, sys, codecs, getopt

from config import BASE_DIR


LANGUAGE = 'en'
                                

def usage():
    print "Usage:"
    print "% python matcher.py [-l LANGUAGE]"



def select(source_dir, phr_occ2_file, phr_occ3_file, phr_occ4_file, language):

    print "Loading results of annotation, classification and matching..."
    
    # use negative samples to reduce number of false positives
    negative_annotation_samples = load_negative_annotation_examples(language)
    print "  Negative samples available from annotation: %s" % \
        len(negative_annotation_samples.keys())

    # get all identifiers of nps in context that were classified as technologies
    technology_nps = load_technology_nps(phr_occ3_file)
    print "  Technology NPs found by classifier: %d " % len(technology_nps.keys())
                                                       
    # get all nps that matched a pattern
    matched_nps = load_matched_nps(phr_occ2_file)
    print \
        "  Matching NPs found by matched: %d (total matches: %s)" % \
        (len(matched_nps.keys()), sum([len(ids) for ids in matched_nps.values()]))
    
    # this file collects all elements that go into the ontology
    out = codecs.open(phr_occ4_file, 'w')

    print "Cheching all NPS in context..."
    subdirs = glob.glob(os.path.join(source_dir, "*"))
    patterns_matched = 0
    technologies_found = 0
    for subdir in subdirs:
        #print subdir
        year = os.path.basename(subdir)
        files = glob.glob(os.path.join(subdir, "*.xml"))
        for fname in files:
            infile = codecs.open(fname)
            for line in infile:
                (match_id, year, term, sentence) = line.strip().split("\t")
                if negative_annotation_samples.has_key(term):
                    continue
                if technology_nps.has_key(match_id):
                    technologies_found += 1
                    patterns = matched_nps.get(match_id, [])
                    if patterns:
                        patterns_matched += len(patterns)
                    patterns_string = ' '.join(patterns)
                    out.write("%s\t%s\t%s\t%s\t[%s]\n" % \
                              (match_id, year, term, sentence, patterns_string))

    print "  Technologies found:", technologies_found
    print "  Associated patterns", patterns_matched
    
    
def load_negative_annotation_examples(language):
    """Returns a dictionary with all negative samples from the annotations file."""
    annotations_file = os.path.join('..', 'annotation', language, 'phr_occ.lab')
    samples = {}
    for line in codecs.open(annotations_file):
        if line.startswith('n'):
            term = line.strip().split("\t")[1]
            samples[term] = True
    return samples


def load_technology_nps(phr_occ3_file):
    technologies = {}
    for line in codecs.open(phr_occ3_file):
        technologies[line.strip()] = True
    return technologies


def load_matched_nps(phr_occ2_file):
    matches = {}
    for line in codecs.open(phr_occ2_file):
        match_id, pattern_id = line.strip().split("\t")
        matches.setdefault(match_id,[]).append(pattern_id)
    return matches




if __name__ == '__main__':

    language = LANGUAGE

    try:
        (opts, args) = getopt.getopt(sys.argv[1:], 'l:', [])
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2)
    for opt, val in opts:
        if opt == '-l': language = val

    source_dir = os.path.join(BASE_DIR, language, 'phr_occ')
    phr_occ2_file = os.path.join(BASE_DIR, language, 'selector', 'phr_occ2_matcher.tab')
    phr_occ3_file = os.path.join(BASE_DIR, language, 'selector', 'phr_occ3_classifier.tab')
    phr_occ4_file = os.path.join(BASE_DIR, language, 'selector', 'phr_occ4_selector.tab')
    
    select(source_dir, phr_occ2_file, phr_occ3_file, phr_occ4_file, language)
