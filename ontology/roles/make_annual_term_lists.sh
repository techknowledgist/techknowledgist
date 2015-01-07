# create a file containing all terms found within a set of domains for a given year 

# get start time to compute elapsed time
START_TIME=$(date +%s)

# get path info
source ./roles_config.sh

CORPUS_LIST='ln-us-A21-computers ln-us-A22-communications ln-us-A23-semiconductors ln-us-A24-optical-systems ln-us-A25-chemical-engineering ln-us-A26-organic-chemistry ln-us-A27-molecular-biology ln-us-A28-mechanical-engineering ln-us-A29-thermal-technology ln-us-A30-electrical-circuits'

# For each year, we calculate all terms (.termslist), seen terms so far (.seen), and new terms this year (.neo)
# We need to distinguish the base_year since there is no previous year for it.
BASE_YEAR=1997
START_YEAR=1997
#END_YEAR=1998
END_YEAR=2007

YEAR=$START_YEAR
while [ $YEAR -le $END_YEAR ] ; do
    TERMSLIST_FILE="$LOCAL_CORPUS_ROOT/all/data/tv/$YEAR.termslist"
    echo "TERMS_LIST_FILE: $TERMSLIST_FILE"

    CAT_LIST=""
    # create the full file path list of .terms files for the year
    for CORPUS in $CORPUS_LIST; do
	TERMS_FILE="$LOCAL_CORPUS_ROOT/$CORPUS/data/tv/$YEAR.terms"
	CAT_LIST="$CAT_LIST $TERMS_FILE"
    done

    #echo "CAT_LIST: $CAT_LIST"

    # filter out unlikely terms with punctuation or which contain no alpha chars (NOTE: English dependency!)
    # remove terms with > 100 chars.
    #cat $CAT_LIST | cut -f1 | egrep "[a-z]" | egrep -v "^[!'.-]" | egrep -v "[#%_+,]" | sed -e '/.\{100\}$/d' | sort | uniq > $TERMSLIST_FILE 
    # restrict terms to alpha, space, apostrophe and dash (and first char must be alpha)
    cat $CAT_LIST | cut -f1 | egrep "^[a-z' -]*$" | egrep -v "^['-]" | sed -e '/.\{100\}$/d' | sort | uniq > $TERMSLIST_FILE 

    # also keep a file with doc freq of each term, and a numeric index for the source corpus (corresponding to
    # the order of domains in the corpus_list
    FREQ_FILE="$LOCAL_CORPUS_ROOT/all/data/tv/$YEAR.freq"
    # empty the freq_file if it already exists, since we will be appending to it in the loop below
    > $FREQ_FILE
    SORTED_FREQ_FILE="$FREQ_FILE.sorted"

    DOMAIN_NO=0    
    for DOMAIN_FILE in $CAT_LIST; do

	#echo "Processing DOMAIN_NO: $DOMAIN_NO"
	# use double quotes around sed expression in order for shell variables to be evaluated (e.g., $DOMAIN_NO)
	# in sed "$" in pattern means end of line
	cat $DOMAIN_FILE | cut -f1,2 | egrep "^[a-z' -]*	" | egrep -v "^['-]" | sed -e '/.\{100\}	/d' | sed -e "s/\$/\t$DOMAIN_NO/" >> $FREQ_FILE
	
	DOMAIN_NO=$[ $DOMAIN_NO + 1 ]
    done
    
    sort $FREQ_FILE > $SORTED_FREQ_FILE
    # we no longer need the unsorted freq_file
    rm $FREQ_FILE

    PREV_YEAR=$[ $YEAR - 1 ]
    SEEN_FILE="$LOCAL_CORPUS_ROOT/all/data/tv/$YEAR.seen"
    PREV_SEEN_FILE="$LOCAL_CORPUS_ROOT/all/data/tv/$PREV_YEAR.seen"
    NEO_FILE="$LOCAL_CORPUS_ROOT/all/data/tv/$YEAR.neo"


    if [ "$YEAR" -ne "$BASE_YEAR" ]
	then
	echo "in if then for year: $YEAR"
	cat $TERMSLIST_FILE $PREV_SEEN_FILE | sort | uniq > $SEEN_FILE
	# do unix join on sorted files to get terms appearing in current termslist but not in previous year's seen file
	join -v2 -t"	" $PREV_SEEN_FILE $TERMSLIST_FILE > $NEO_FILE
	
	else
	echo "in if else for year: $YEAR"
	# for the base year, the seen file is a copy of the termslist file
	cp $TERMSLIST_FILE $SEEN_FILE
	
    fi

    YEAR=$[ $YEAR + 1 ]


done



