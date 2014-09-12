# general python utilities, including log functions

import sys
import re
import datetime


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

# return intersection of two lists, preserves order in the first list
def intersect(seq1, seq2):
    _auxset = set(seq2)
    return [x for x in seq1 if x in _auxset]

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


# takes a datetime, output stream, message
# computes the time elapsed in seconds and writes it to the output stream
# e.g. Fri Nov 16 14:12:16 2012        63      time 2
# returns the current datetime object which can be used as prev_time in a subsequent call.
def log_time_diff(prev_time, log_stream, message, print_p = True):
    now_time = datetime.datetime.now()
    diff = now_time - prev_time
    ctime = now_time.ctime()
    # e.g. 'Fri Nov 16 13:18:42 2012'
    if print_p:
        print("%s\t%s\t%s\n" % (ctime, diff.seconds, message)) 
    log_stream.write("%s\t%s\t%s\n" % (ctime, diff.seconds, message))
    # flush line so we can track progress through the log
    log_stream.flush()
    return(now_time)

# log current time in same format as log_time_diff (using 0 seconds as diff)
# e.g. Fri Nov 16 14:11:13 2012        0       time 1
def log_current_time(log_stream, message, print_p = True):
    now_time = datetime.datetime.now()
    ctime = now_time.ctime()
    # e.g. 'Fri Nov 16 13:18:42 2012'
    if print_p:
        print("%s\t%s\t%s\n" % (ctime, "0", message)) 
    log_stream.write("%s\t%s\t%s\n" % (ctime, "0", message)) 
    # flush line so we can track progress through the log
    log_stream.flush()

    return(now_time)



if __name__ == '__main__':

    s1 = [1,2,3,4,5,6]
    s2 = [1,8,5,6]
    print intersect(s1, s2)


    
