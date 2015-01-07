# lifecycle.py 
# 

"""
After running sh  make_annual_term_lists.sh
/home/j/anick/patent-classifier/ontology/roles/data/patents/all/data/tv contains, for every year in range
2007.freq.sorted  : term  freq  domain_no   (doc freq for each term within the indicated domain)
2007.neo  : terms which first appear in this year's documents
2007.seen  : terms which appeared either in this year or any prior year
2007.termslist  : full list of terms appearing this year

There is no .neo file for the start year (1997), since this is the first year for which 
we have term data, at the moment. 

To get a total frequency for each term per year (across all domains), we need to sum over entries in .freq.sorted

(1) build a dict of all seen terms


"""

