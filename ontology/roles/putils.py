# putils.py  (name changed from utils.py to avoid name conflict with Marc Verhagen's file)
# general python utilities

import sys
import re

# descending sort based on 2nd element of list item
def list_element_2_sort(e1, e2):
    diff = e2[1] - e1[1]
    if diff > 0:
        return 1
    elif diff < 0:
        return -1
    else:
        return 0

# ascending alphabetic sort on 1st element of list item
def list_element_1_sort(e1, e2):
    return(cmp(e1[0],e2[0]))

def intersect(seq1, seq2):
    res = []
    for x in seq1:
        if x in seq2:
            if x not in res:
                res.append(x)
    return res

# extract the file name from a full path
def path2filename(path, extension_p):
    filename = path[path.rfind("/")+1:len(path)]
    if extension_p == 0:
        # remove extension
        filename = filename[0:filename.rfind(".")]
        
    return filename

# get the last word in a blank separated field
def get_last_word(field):
    #return([field, field[field.rfind(" ")+1:]  ])
    return(field[field.rfind(" ")+1:]  )

def get_field_after(field, split_word):
    # match will be the split_word surrounded by blanks
    # i.e. embedded inside a field of blank separated words
    split_match = " " + split_word + " "
    parts = field.split(split_match)
    if len(parts) > 1:
        return([split_word, parts[1], parts[0]])
    else:
        return ""



# reformat output of unix uniq -c | sort -nr
# to <count>\t<value>
def reformat_uc():
    for line in sys.stdin:
        line = line.strip("\n")
        line = line.lstrip(" ")
        count = line[0:line.find(" ")]
        value = line[line.find(" ")+1:]
        #print "count: %s, value %s" % (count, value)
        newline = count + "\t" + value
        print newline



# replace cases of &apos; and &quot; with original punctuation
def restore_line_punc(line):
    line = re.sub(r'&apos;', "'", line)
    line = re.sub(r'&quot;', '"', line)
    line = re.sub(r'&lt;', '<', line)
    line = re.sub(r'&gt;', '>', line)

    return line
