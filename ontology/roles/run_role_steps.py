# called by run_role_steps.sh

# 

import role
import nbayes
import sys

if __name__ == "__main__":
    args = sys.argv
    corpus = args[1]
    year = args[2]
      
    # default steps to be run for ACT classification
    ACT_steps = ["tc", "tcs", "fc", "uc", "prob", "train"]
    # only do the "tf" step if requested by caller setting the third parameter to True
    if len(sys.argv) > 3:
        do_tf_p = args[3]
    else:
        do_tf_p = False

    if do_tf_p == "True":
        ACT_steps = ["tf", "tc", "tcs", "fc", "uc", "prob", "train"]


    print "do_tf_p: %s, ACT_steps: %s" % (do_tf_p, ACT_steps)
    #sys.exit()


    role.run_tf_steps(corpus, year, year, "act", ACT_steps)  
    print "[run_role_steps.py]Completed run_role_steps.py (ACT analysis)"
    nbayes.run_steps(corpus, year, ["nb", "ds", "cf"])
    print "[run_role_steps.py]Completed run_steps (ACT nbayes)"

    nbayes.run_filter_tf_file(corpus, year, "0.0") # create a.tf, needed for running polarity
    print "[run_role_steps.py]Completed run_filter_tf_file"
    role.run_tf_steps(corpus, year, year, "pn", ["tc", "tcs", "fc", "uc", "prob"], "a")  
    print "[run_role_steps.py]Completed run_role_steps.py (Polarity analysis)"
    nbayes.run_steps(corpus, year, ["nb", "ds", "cf"], cat_type="pn", subset="a")
    print "[run_role_steps.py]Completed run_steps (Polarity nbayes)"
