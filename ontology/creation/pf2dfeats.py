# convert a file of phrase occurrence features (phr_feats)
# to a file with one (summed) set of features per phrase (doc_feats)

import collections
import os

def make_doc_feats(phr_feats, doc_feats, doc_id, year):
    s_phr_feats = open(phr_feats)
    s_doc_feats = open(doc_feats, "w")
    
    # map phrase to features
    d_p2f = {}
    for line in s_phr_feats:
        line = line.strip("\n")
        #print "\n[make_doc_feats]line: |%s|" % line
        l_feat = line.split("\t")
        # key is the chunk itself
        key = l_feat[2]
        #print "key: %s, l_feat: %s" % (key, l_feat[3:])
        feats = l_feat[3:]
        if d_p2f.has_key(key):
            l_current_feat = d_p2f.get(key)
            #if l_current_feat == None:
            #    print "key: %s has None value: |%s|" % (key, l_current_feat) 
            l_new_feat = []
            # merge the new feats
            for feat in feats:
                #print "[2]feat: %s, l_current_feat: %s" % (feat, l_current_feat)

                
                if feat not in l_current_feat:
                    l_new_feat.append(feat)
            #extension = l_current_feat.extend(l_new_feat)
            # extend the key value in place (note that extend doesn't return a value, it modifies the list directly)
            d_p2f[key].extend(l_new_feat)
            #print "Extended |%s| with |%s|" % (l_current_feat, l_new_feat)
            #print "key: %s, value: |%s|" % (key, extension)
        else:
            #print "***********[make_doc_feats]New key: %s, feats: |%s|" % (key, feats)
            d_p2f[key] = feats


    for key in d_p2f.keys():
        # remember that key is the phrase (i.e., chunk)
        symbol_key = key.replace(" ", "_")
        uid = year + "|" + doc_id + "|" + symbol_key
        feat_string = key + "\t" + uid + "\t" + "\t".join(d_p2f.get(key)) + "\n"
        s_doc_feats.write(feat_string)

    s_phr_feats.close()
    s_doc_feats.close()

def pf2dfeats_dir(phr_feats_year_dir, doc_feats_year_dir, year):
    for file in os.listdir(phr_feats_year_dir):
        input = os.path.join(phr_feats_year_dir, file)
        output = os.path.join(doc_feats_year_dir, file)
        (doc_id, extension) = file.split(".")
        make_doc_feats(input, output, doc_id, year)

# e.g. tag2chunk.patent_tag2chunk_dir("/home/j/anick/fuse/data/patents", "de")
def patent_pf2dfeats_dir(patent_path, language):
    lang_path = patent_path + "/" + language
    phr_feats_path = lang_path + "/phr_feats"
    doc_feats_path = lang_path + "/doc_feats"
    for year in os.listdir(phr_feats_path):
        phr_feats_year_dir = phr_feats_path + "/" + year
        doc_feats_year_dir = doc_feats_path + "/" + year
        print "[patent_pf2dfeats_dir]calling pf2dfeats for dir: %s" % phr_feats_year_dir
        pf2dfeats_dir(phr_feats_year_dir, doc_feats_year_dir, year)
    print "[patent_pf2dfeats_dir]finished creating doc_feats in: %s" % (doc_feats_path)


def pipeline_pf2dfeats_dir(root, language):

    phr_feats_path = root + "/phr_feats"
    doc_feats_path = root + "/doc_feats"
    # The only way to determine the year for a file is to look in file_list.txt
    file_list_file = os.path.join(root, "file_list.txt")
    s_list = open(file_list_file)
    year = ""
    file_path = ""
    for line in s_list:
        (id, year, path) = line.split(" ")
        # create the file name from id + .xml
        file_name = id + ".xml"

        phr_feats_file = os.path.join(phr_feats_path, file_name)
        doc_feats_file = os.path.join(doc_feats_path, file_name)

        make_doc_feats(phr_feats_file, doc_feats_file, id, year)
    s_list.close()

# pf2dfeats.test_p2d()
def test_p2d():
    input_phr_feats = "/home/j/anick/fuse/data/patents/en_test/phr_feats/US20110052365A1.xml"
    output_doc_feats = "/home/j/anick/fuse/data/patents/en_test/doc_feats/US20110052365A1.xml"
    year = "1980"
    (doc_id, extension) = input_phr_feats.split(".")
    make_doc_feats(input_phr_feats, output_doc_feats, doc_id, year)
