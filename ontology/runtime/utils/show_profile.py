"""

Show statistics from the profiler.

Usage:

    $ python show_profile.py ../workspace/saved-profiles/004

    This shows the statistics from all profile files in the directory, profile
    files are all expected to start with 'profile-'.

"""

import sys, pstats, glob

for stats in glob.glob(sys.argv[1] + '/profile-*'):
    p = pstats.Stats(stats)
    #p.strip_dirs().sort_stats(-1).print_stats()
    #p.strip_dirs().sort_stats('time').print_stats(10)
    p.strip_dirs().sort_stats('cumulative').print_stats()
