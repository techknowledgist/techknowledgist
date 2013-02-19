# utilities for manipulating annotation files (.lab, .unlab)
# PGA


# merge annotation files as follows:
# target contains the list of terms that will go into merged.  If a term is labeled, this label will be included.
# source contains terms, some with labels.  For any term in target without a label, the source label will
# go to merged. If source label differs from target label, the source line is written to conflicts file.

# So if target contains all terms in a subset of documents and source contains many terms with labels from some
# larger set, this is a way to merge labels from source into the target term subset.
# Example: ts10 is a subset of 10 out of 500 patents to be used for evaluation.
# ts490 are the terms in the remaining 490 patents (training docs).

# files should be in the form: <optional label char><tab><phrase>
# Move any labels in source for terms appearing in target into merged, except for conflicts, which are
# written to conflicts file.  Unlabeled terms within target are also included in merged.
# All files should be full pathnames

import sys

def merge_labs(source, target, merged, conflicts):
    s_target = open(target, "r")
    s_source = open(source, "r")
    s_merged = open(merged, "w")
    s_conflicts = open(conflicts, "w")

    # load the labels for source into a dictionary)
    d_source = {}
    source_total = 0
    source_count = 0
    target_count = 0
    conflict_count = 0

    # store the labels in source
    for line in s_source:
        (label, phrase) = line.strip("").split("\t")
        if label != "":
            source_count += 1
            d_source[phrase] = label
            #print "label: %s, phrase: %s" % (label, phrase)
        source_total += 1
    
    print "labels: %i, source phrases: %i" % (source_count, source_total)

    # merge with labels in target
    for line in s_target:
        (target_label, phrase) = line.strip("").split("\t")
        # set default source label
        source_label = ""
        # check if there is a source label
        if d_source.has_key(phrase):
            source_label = d_source[phrase]
                
            if target_label == "" or target_label == source_label:
                s_merged.write("%s\t%s" % (source_label, phrase))
                target_count += 1
            else:
                # keep the target label and store the conflict
                s_merged.write("%s\t%s" % (target_label, phrase))
                s_conflicts.write("%s\t%s" % (source_label, phrase))
                conflict_count += 1

        # handle case where target has a label but source does not
        elif target_label != "":
            s_merged.write("%s\t%s" % (source_label, phrase))
            target_count += 1            

    print "target_count: %i, conflict_count: %i" % (target_count, conflict_count)
    

    s_target.close()
    s_source.close()
    s_merged.close()
    s_conflicts.close()


# put labeled items in source into diff, excluding any labeled terms in exclude.
# This allows us to train on a set of terms (diff), none of which are in the evaluation set (exclude).
def diff_labs(source, exclude, diff):
    s_exclude = open(exclude, "r")
    s_source = open(source, "r")
    s_diff = open(diff, "w")
    
    # load the labels for source into a dictionary)
    d_exclude = {}
    exclude_total = 0
    source_count = 0
    exclude_count = 0
    diff_count = 0

    # store the terms in exclude
    for line in s_exclude:
        (label, phrase) = line.strip("").split("\t")
        if label != "":
            exclude_count += 1
            d_exclude[phrase] = label
            #print "label: %s, phrase: %s" % (label, phrase)
        exclude_total += 1
    
    print "exclude phrases: %i" % (exclude_count)

    # remove excluded terms from source
    for line in s_source:
        
        (source_label, phrase) = line.strip("").split("\t")
        if source_label != "":

            # check if phrase is an exclude term
            if not d_exclude.has_key(phrase):
                s_diff.write("%s\t%s" % (source_label, phrase))
                diff_count += 1

    print "diff_count: %i" % (diff_count)
    

    s_exclude.close()
    s_source.close()
    s_diff.close()


    
# 
# annot_utils.t10()
# evaluation terms using new chunker only
def t10():
    #source = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ts1/en/ws/phr_occ.lab.0s"
    #source = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ts1/en/ws/phr_occ.lab.combined"
    source = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ts1/en/ws/all.oldc_newc.20130209.lab"
    target = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ts10/en/ws/phr_occ.unlab"
    merged = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ts10/en/ws/phr_occ.merged"
    conflicts = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ts10/en/ws/phr_occ.conflicts"
    merge_labs(source, target, merged, conflicts)

# annot_utils.t490()
# training terms for new chunker only
def t490():
    #source = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ts1/en/ws/phr_occ.lab.0s"
    #source = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ts1/en/ws/phr_occ.lab.combined"
    source = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ts1/en/ws/all.oldc_newc.20130209.lab"
    target = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ts490/en/ws/phr_occ.unlab"
    merged = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ts490/en/ws/phr_occ.merged"
    conflicts = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ts490/en/ws/phr_occ.conflicts"
    merge_labs(source, target, merged, conflicts)

    # now remove items in the training set
    source = merged
    # note that next line depends on result of running t10 function to create list of evaluation terms
    exclude = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ts10/en/ws/phr_occ.merged"
    diff = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ts490/en/ws/all.oldc_newc.20130209.nc.no_testing.lab" 
    diff_labs(source, exclude, diff)





# see file remove_first_char.py for version to be used in command line.
# This removes the label character from a fully annotated annotation (.lab) file.
# Note: it does not check whether a label exists before removing the first character!
def remove_first_char():
    for line in sys.stdin:
        print line[1:]

# annot_utils.diff_training()
# This training set is useful for old and new chunker, since we don't merge (intersect) the initial set of annotations
# with the set of new chunker terms.
def diff_training_set():
    source = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ts1/en/ws/all.oldc_newc.20130209.lab"
    exclude = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ts10/en/ws/phr_occ.nc.eval.lab.labeled_only"
    diff = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ts1/en/ws/all.oldc_newc.20130209.no_testing.lab"
    diff_labs(source, exclude, diff)



if __name__ == '__main__':

    if sys.argv[1] == 'diff':
        (source, exclude, diff) = sys.argv[2:5]
        diff_labs(source, exclude, diff)

    elif sys.argv[1] == 'merge':
        (source, target, merge, conflicts) = sys.argv[2:6]
        merge_labs(source, target, merge, conflicts)
