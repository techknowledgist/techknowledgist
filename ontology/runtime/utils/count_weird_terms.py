import sys, re, codecs

regexp = re.compile("[a-z]\d+[a-z]")

first_token_file = 'all_terms.az.first_token.uniq.txt'
outfile = codecs.open(sys.argv[1], 'w', encoding='utf-8')

fh = codecs.open(first_token_file, encoding='utf-8')

for line in fh:
    if regexp.search(line) is not None:
        outfile.write(line)
    
