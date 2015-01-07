# log functions

import datetime

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





    
