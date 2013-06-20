"""
Loading this module adjust sys.path by adding the root directory of the
patent-classifier code. It does not add this root directory if it is already in
the path. Note that this check is probably not needed because path will be
imported only once no matter how often you import it in other modules.

"""

import os, sys

script_path = os.path.abspath(sys.argv[0])
script_dir = os.path.dirname(script_path)

if not sys.path[0] == script_dir:
    os.chdir(script_dir)
    os.chdir('../..')
    sys.path.insert(0, os.getcwd())
    os.chdir(script_dir)
    
