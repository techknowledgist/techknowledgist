"""

Counting tags from all tagged files in a directory (that is, all files with the
.tag extension).

Usage:
    
    $ python count_tags.py ../workspace/tmp

This was run on the 200 sample files in order to find tokens that are function
words and likely to be not in a chunk (prepositions) or be the beginning of a
chunk (determiners).

Notable results:

    CC - + AND and and\/or both but either or
    
    DT - A An Any Each No THE The These This a all an another any both each
         either no some that the these this those

    IN - After As At By During FOR For IN If In Next Since Through Upon With
         about above across after against along although among amongst as at
         because before below beneath between beyond by during except for from
         if in inside into near next of off on onto out outside over per so than
         that though through toward under unless until up upon via whether while
         with within without

    RP - down in off on out over

    TO - to
    
"""


import sys, glob, codecs


dirname = sys.argv[1]

FUNCTION_TAGS = dict.fromkeys(['IN', 'DT', 'CC', 'RP', 'TO'], True)

TAGS1 = {}

TAGS2 = {}


for fname in glob.glob("%s/*tag" % dirname):
    print fname
    for line in codecs.open(fname, encoding='utf-8'):
        if line.startswith('FH_'):
            continue
        tokens = line.strip().split()
        #print tokens
        for pair in tokens:
            try:
                token, tag = pair.split('_')
                #print token, tag
                TAGS1[tag] = TAGS1.get(tag, 0) + 1
                if not TAGS2.has_key(tag):
                    TAGS2[tag] = {}
                TAGS2[tag][token] = TAGS2[tag].get(token, 0) + 1
            except ValueError:
                print "Skipping", pair

for tag in sorted(TAGS1.keys()):
    print tag, TAGS1[tag]

for tag in sorted(TAGS2.keys()):
    if FUNCTION_TAGS.has_key(tag):
        print tag
        token_list = []
        for token in sorted(TAGS2[tag].keys()):
            token_list.append(token)
            count = TAGS2[tag][token]
            #print '  ', token, count
        token_list = list(set([t.lower() for t in token_list]))
        print len(token_list), sorted(token_list)
