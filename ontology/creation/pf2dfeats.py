# convert a file of phrase occurrence features (phr_feats)
# to a file with one (summed) set of features per phrase (doc_feats)

import collections


def make_doc_feats(phr_feats, doc_feats):
    s_phr_feats = open(phr_feats)
    s_doc_feats = open(doc_feats, "w")
    
    # map phrase to features
    d_p2f = {}
    for line in s_phr_feats:
        line = line.strip("\n")
        #print "\n[make_doc_feats]line: |%s|" % line
        l_feat = line.split("\t")
        key = l_feat[0]
        #print "key: %s, l_feat: %s" % (key, l_feat[1:])
        feats = l_feat[1:]
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
            # extend the key value in place (extend doesn't return a value, it modifies the list directly)
            d_p2f[key].extend(l_new_feat)
            #print "Extended |%s| with |%s|" % (l_current_feat, l_new_feat)
            #print "key: %s, value: |%s|" % (key, extension)
        else:
            #print "***********[make_doc_feats]New key: %s, feats: |%s|" % (key, feats)
            d_p2f[key] = feats


    for key in d_p2f.keys():
        feat_string = key + "\t" + "\t".join(d_p2f.get(key)) + "\n"
        s_doc_feats.write(feat_string)

    s_phr_feats.close()
    s_doc_feats.close()

# pf2dfeats.test_p2d()
def test_p2d():
    input_phr_feats = "/home/j/anick/fuse/data/patents/en_test/phr_feats/US20110052365A1.xml"
    output_doc_feats = "/home/j/anick/fuse/data/patents/en_test/doc_feats/US20110052365A1.xml"
    make_doc_feats(input_phr_feats, output_doc_feats)
