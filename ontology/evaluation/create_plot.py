"""

Script to create latex plots from a text strings as in PLOT_DATA_N below. It is geared
towards creating the plots for the evaluation described in technology-classifier.txt.


Assumes:
    
    - an x-axis with values from 0.0-0.9 and a y-axis with values from 0.0-1.0.
    - thresholds to be on the x-axis
    - precision and recall values on the y-axis
    
"""

import sys


def create_plot(text, fh=sys.stdout):

    thresholds = []
    graphs = {}

    for line in text.split("\n"):
        if line.strip() == '':
            continue
        if line[0].isalnum():
            name = line.strip()
        else:
            values = line.strip().split()
            sequence_name = values.pop(0)
            if sequence_name == 'threshold':
                thresholds = values
            else:
                graphs[sequence_name] = values

    fh.write("\n\\begin{figure}[ht]\n")
    fh.write("\\centering\n")
    fh.write("\\begin{tikzpicture}[scale=0.8]\n")
    fh.write("\\begin{axis}[\n")
    fh.write("   xlabel=Classifier Probability Threshold,\n" + \
          "   width=5.5in, height=3in,\n" + \
          "   xmin=0, xmax=0.9, ymin=0, ymax=1,\n" + \
          "   inner sep=5pt,\n" + \
          "   %s,\n" % legend_style(name) + \
          "   grid=major ]\n\n")
    
    for sequence_name, sequence in graphs.items():
        fh.write("   \\addplot[color=%s, mark=+] coordinates {\n" % set_color(sequence_name))
        for i in range(10):
            fh.write("      (%s, %s)\n" % (thresholds[i], sequence[i]))
        fh.write("   };\n")
        fh.write("   \\addlegendentry{%s}\n\n" % sequence_name)

    fh.write("\\end{axis}\n")
    fh.write("\\end{tikzpicture}\n")
    fh.write("\\caption{%s}\n" % name)
    fh.write("\\end{figure}\n")
    

def set_color(sequence_name):
    if sequence_name == 'precision': return 'red'
    if sequence_name == 'recall': return 'blue'
    if sequence_name.startswith('standard'): return 'red'
    if sequence_name.startswith('variant1'): return 'blue'
    if sequence_name.startswith('variant2'): return 'green'

def legend_style(name):
    coordinates = "0.85,0.95"
    columns = "-1"
    if name == "Comparing precision":
        coordinates = "0.50,3.95"
        columns = "1"
    elif name == "Comparing recall":
        coordinates = "0.95,0.95"
        columns = "1"
    return "legend style={at={(%s)},legend columns=%s}" % (coordinates, columns)



PLOT_DATA_1 = """

standard-1a2a3b4a

	threshold   0.0  0.1  0.2  0.3  0.4  0.5  0.6  0.7  0.8  0.9
	precision   0.33 0.41 0.44 0.49 0.53 0.59 0.62 0.64 0.67 0.70 
	recall      1.00 0.93 0.74 0.59 0.47 0.43 0.32 0.22 0.16 0.11
"""

PLOT_DATA_2 = """

variant1-1a2a3a4a

	threshold   0.0  0.1  0.2  0.3  0.4  0.5  0.6  0.7  0.8  0.9
	precision   0.32 0.38 0.42 0.46 0.54 0.61 0.69 0.74 0.75 0.90 
	recall      1.00 0.94 0.83 0.67 0.52 0.38 0.29 0.20 0.15 0.08
"""

PLOT_DATA_3 = """

variant2-1a2a3b4b

	threshold   0.0  0.1  0.2  0.3  0.4  0.5  0.6  0.7  0.8  0.9
	precision   0.34 0.41 0.43 0.49 0.53 0.59 0.61 0.64 0.66 0.71 
	recall      1.00 0.92 0.73 0.57 0.45 0.40 0.30 0.20 0.14 0.10
"""

PLOT_DATA_4 = """

Comparing precision

	threshold          0.0  0.1  0.2  0.3  0.4  0.5  0.6  0.7  0.8  0.9
	standard-1a2a3b4a  0.33 0.41 0.44 0.49 0.53 0.59 0.62 0.64 0.67 0.70 
	variant1-1a2a3a4a  0.32 0.38 0.42 0.46 0.54 0.61 0.69 0.74 0.75 0.90 
	variant2-1a2a3b4b  0.34 0.41 0.43 0.49 0.53 0.59 0.61 0.64 0.66 0.71     
"""

PLOT_DATA_5 = """

Comparing recall

	threshold          0.0  0.1  0.2  0.3  0.4  0.5  0.6  0.7  0.8  0.9
	standard-1a2a3b4a  1.00 0.93 0.74 0.59 0.47 0.43 0.32 0.22 0.16 0.11
	variant1-1a2a3a4a  1.00 0.94 0.83 0.67 0.52 0.38 0.29 0.20 0.15 0.08
	variant2-1a2a3b4b  1.00 0.92 0.73 0.57 0.45 0.40 0.30 0.20 0.14 0.10
"""



if __name__ == '__main__':

    PLOT_DATA = [PLOT_DATA_1, PLOT_DATA_2, PLOT_DATA_3, PLOT_DATA_4, PLOT_DATA_5]
    fh = open("plots.tex", 'w')
    for PLOT in PLOT_DATA:
        create_plot(PLOT, fh)
