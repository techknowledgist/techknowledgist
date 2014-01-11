"""

Script to run a few files throught hhe segmenter.

Usage:

    $ run_segmenter.py file1 file2 ...

    For each file an output file is created with the .seg extention.
    
"""


import os, sys

import sdp
import cn_txt2seg

sys.path.append(os.path.abspath('../..'))

from ontology.utils.file import uncompress


files_in = sys.argv[1:]

segmenter = sdp.Segmenter()
swrapper = cn_txt2seg.SegmenterWrapper(segmenter)

use_old = True
use_old = False

for file_in in files_in:
    uncompress(file_in)
    file_out = file_in + '.seg'
    if use_old:
        cn_txt2seg.seg(file_in, file_out, segmenter)
    else:
        swrapper.process(file_in, file_out, verbose=True)
