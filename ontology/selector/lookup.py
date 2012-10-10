import shelve, sys

language = sys.argv[1]
INDEX_FILE = "/Users/marc/Desktop/FUSE/ontology_creation/data/patents/%s/idx/index" % language
INDEX = shelve.open(INDEX_FILE)

print "Searching index with %d keys" % len(INDEX.keys())

while True:
    print "Enter a key:"
    term = raw_input()
    if not term:
        break
    if INDEX.has_key(term):
        for y in sorted(INDEX[term].keys()):
            print "  %s %3d" % (y, INDEX[term][y])
    else:
        print "  Not in index"
