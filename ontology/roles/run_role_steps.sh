# run all the steps to do ACT and polarity analysis for a given corpus and year
# Assumes that run_term_features.sh has already been run to create the necessary prerequisite files
# Assumes config info ($LOCAL_CORPUS_ROOT) is set in roles_config.py and roles_config.sh

# note the 3rd parameter is set to True if you need run_role_steps.py to create the .tf, .terms,
# .feats, and .c files.  If these have already been created, the arg should be set to False

# e.g., 
# sh run_role_steps.sh ln-us-A28-mechanical-engineering 2002 False
# sh run_role_steps.sh ln-us-A21-computers_test_pa 2002 False

# get start time to compute elapsed time
START_TIME=$(date +%s)

# get path info
source ./roles_config.sh

CORPUS=$1
YEAR=$2
RUN_TF_P=$3

python run_role_steps.py $CORPUS $YEAR $RUN_TF_P
echo "[run_role_steps.sh after ACT and polarity analysis]Elaspsed time: $(date -d @$(($(date +%s)-$START_TIME)) +"%M minutes %S seconds")"