import sys, getopt

def read_opts(short, long, usage_function):
    try:
        (opts, args) = getopt.getopt(sys.argv[1:], short, long)
        return (opts, args)
    except getopt.GetoptError, err:
        print str(err)
        usage_function()
        sys.exit(2)


def write_histogram(fh, term, frequencies):

    years = sorted(frequencies.keys())
    y1 = min(int(years[0]), 1980)
    y2 = max(int(years[-1]) + 1, 2012)
        
    all_years = range(y1, y2+1)
    all_frequencies = {}
    total = sum(frequencies.values())
    for year in all_years:
        freq = frequencies.get(str(year), 0)
        all_frequencies[year] = (float(freq)/total) *10

    for f in (10,9,8,7,6,5,4,3,2,1):
        fh.write("%3s" % str(f * 10) + '% | ')
        for y in all_years:
            bars = '-- ' if all_frequencies[y] > f-1 else '   '
            fh.write(bars)
        fh.write("\n")
    fh.write("     +-")
    for y in all_years:
        fh.write('---')
    fh.write('-')
    fh.write("\n       ")
    for y in all_years:
        x_axis = str(y)[2:] + ' ' if y % 5 == 0 else '   '
        fh.write(str(x_axis))


html_prefix = """
<html>
<head>
<style>
term { color: darkblue; font-weight: bold}
np { color: darkblue; font-weight: bold}
</style>
</head>
<body>
"""

html_end = """
</body>
</html>
"""

html_explain = """
<html>
<body>
<h2>Interpreting the term distribution figure</h2>

<p>This figure shows the distribution per year of term mentions in reference data for the
term "user interface".</p>

<blockquote>
<pre>
100% |                                                                   
 90% |                                                                   
 80% |                                                                   
 70% |                                                                   
 60% |                                                                   
 50% |                                                             --    
 40% |                                                             --    
 30% |                                                           ----    
 20% |                                                           ----    
 10% |                                             --  --------  ------  
     +--------------------------------------------------------------------
       80        85        90        95        00        05        10    </pre>
</blockquote>

<p>The height of the vertical bar for a year reflects the percentage of all term mentions
in that year relative to the total. Values are rounded up. For example, mentions of "user
interface" in 2009 comprise > 20% of the total but <= 30%.</p>

</body>
</html>
"""

