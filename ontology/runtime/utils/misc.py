import time

def default_id():
    """Returns a string represenatation of the current timestamp."""
    return time.strftime('%Y%m%d-%H%M%S')


def read_filelist(filelist):
    """Read the files in the input filelist. Allows each line to either have
    both the path to the text file and fact file or just a path without the
    extension."""
    infiles = []
    for line in open(filelist):
        files = line.strip().split("\t")
        if len(files) == 1:
            infiles.append([files[0]+'.txt', files[0]+'.fact'])
        elif len(files) == 2:
            infiles.append([files[0], files[1]])
        else:
            print "WARNING: unexpected line in filelist"
            print "        ", line
    return infiles

