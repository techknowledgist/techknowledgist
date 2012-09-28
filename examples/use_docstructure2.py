import os, sys

main_dir = '/home/j/corpuswork/fuse/code/patent-classifier'
docstructure_dir = main_dir + '/utils/docstructure'

# add docstructure module to the path
sys.path.insert(0, main_dir)
sys.path.insert(0, docstructure_dir)

# define a namespace and execute the file in that name space
docstructure_namespace = {}
execfile("../utils/docstructure/main.py", docstructure_namespace)

print 'docstructure_namespace:'
for key in sorted(docstructure_namespace.keys()): print ' ', key

# pop the module off the path
sys.path.pop(0)

# you cannot refer to the local utils, I can only assume that inserting docstructure_dir
# into the path has lasting effects, even after you have removed it
try:
    import utils.test
except ImportError:
    print "Error importing utils.test"

# but you can use the full module path
import examples.utils.test
print "Succeeded importing with examples.utils.test"

# finally, you can now run the parser, except that the code depends on access to __file__,
# which in this case we do not have
os.chdir(docstructure_dir)
parser = docstructure_namespace['Parser']()
try:
    parser.ping()
except NameError, e:
    print "ERROR:", e
