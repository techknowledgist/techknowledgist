import os, sys

script_path = os.path.abspath(sys.argv[0])
script_dir = os.path.dirname(script_path)
code_dir = os.path.split(script_dir)[0]

print 1, script_path
print 2, script_dir
print 3, code_dir

sys.path.append(code_dir)

print sys.path
import utils.docstructure

