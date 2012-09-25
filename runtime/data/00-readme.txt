list-CH-*.txt
list-DE-*.txt
list-US-*.txt

	lists for each language of the 500 released patents
	both sorted and random versions, created by

	sort list-CN.txt > list-CN-sorted.txt

	cat list-CN.txt 
		| perl -MList::Util -e 'print List::Util::shuffle <>' 
		> list-CH-random.txt

	the originals lists have since been removed bwere created, but were probably
	created using a find on 
	/home/j/corpuswork/fuse/fuse-patents/500-patents/DATA/Lexis-Nexis/
