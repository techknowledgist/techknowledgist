import os, sys

# go to the directory where the docstructure module lives
saved_dir = os.getcwd()
os.chdir('../utils')

# add it to the beginning of the path
sys.path.insert(0, os.getcwd())

# change directory into docstructure directory
os.chdir('docstructure')

# do what you need to do
from docstructure.main import Parser
Parser().ping()

# revert to the old situation
sys.path.pop(0)
os.chdir(saved_dir)

# now import local utils to demonstrate that there was no conflict
from utils import test


# Actually, the latter is a mirage and I do not understand why this works. Suppose we
# would have done the following INSTEAD of the above:
#
#    saved_dir = os.getcwd()
#    os.chdir('../utils/docstructure')
#    sys.path.insert(0, os.getcwd())
#    from main import Parser
#    Parser().ping()
#    sys.path.pop(0)
#    os.chdir(saved_dir)
#    from utils import test
#
# In that case, the last line would have failed. To confuse me further, if you do these
# line AFTER the lines above, then you fail on importing the parser.
