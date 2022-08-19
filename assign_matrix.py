#! /usr/bin/python3

# This script generate a LaTeX file to visualize HotCRP review preferences
#
# Usage:
# 1. To display preferences:
# python3 assign_matrix.pl allprefs.csv > matrix.tex
# 2. To display preferences and assignment:
# python3 assign_matrix.pl allprefs.csv pcassignment.csv > matrix.tex

# CSV file can be downloaded by selecting all papers, clicking download
# and selecting "PC review preferences"
# If there is a 'Pages' field in the sumbission form, a CSV file with paper
# lengths can be download using the "CSV" option under download

def usage():
    print("Usage: {} allprefs.csv [pcassignment.csv] [-b] [-s] [-o] [-l data.csv]".format(sys.argv[0]))    
    print("\nOptions:")
    print("  -b or --black: black and white output")
    print("  -s or --scale: autoscale preferences according to individual min/max (otherwise assume -20/20)")
    print("  -o or --order: reorder papers and reviewers to move high score to the diagonal")
    print("  -l or --lengths: read paper lengths from CSV file")
    
import csv
import itertools
import re
import math
import functools

import getopt, sys

try:
    opts, args = getopt.gnu_getopt(sys.argv[1:], "bsol:", ["black", "scale", "order", "lengths="])
except getopt.GetoptError as err:
    # print help information and exit:
    print(err)  # will print something like "option -a not recognized"
    usage()
    sys.exit(2)


pref_file = None
assign_file = None
lengths_file = None
opt_black = 0
opt_scale = 0
opt_order = 0

for o, a in opts:
    if o in ("-s", "--scale"):
        opt_scale = 1
    elif o in ("-b", "--black"):
        opt_black = 1
    elif o in ("-o", "--order"):
        opt_order = 1
    elif o in ("-l", "--lengths"):
        lengths_file = a
    else:
        assert False, "unhandled option"

if len(args) == 1:
    pref_file = args[0]
elif len(args) == 2:
    pref_file = args[0]
    assign_file = args[1]
else:
    print ("Error: wrong number of arguments\n")
    usage()
    sys.exit(2)

# Helper function
def latex_encode(text):
    """
        :param text: a plain text message
        :return: the message escaped to appear correctly in LaTeX
    """
    conv = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\^{}',
        '\\': r'\textbackslash{}',
        '<': r'\textless{}',
        '>': r'\textgreater{}',
    }
    regex = re.compile('|'.join(re.escape(str(key)) for key in sorted(conv.keys(), key = lambda item: - len(item))))
    return regex.sub(lambda match: conv[match.group()], text)



# Print LaTeX header
print (r"""\documentclass{standalone}

\usepackage[table]{xcolor}
\usepackage{array,booktabs}
\usepackage{graphicx}
\usepackage{truncate}
\usepackage{soul}
\usepackage{eqparbox}
\usepackage[utf8]{inputenc}

\newif\ifcolor
""")
if opt_black:
    print ("\colorfalse")
else:
    print ("\colortrue")
print(r"""\ifcolor
\definecolor{MyGreen-hsb}{hsb}{0.34065,1,0.91}
\newcommand{\rate}[2]{\ifnum#1=-100%
\color{red!50!black}#2%
\else\ifnum#1=100%
\color{MyGreen-hsb!50!black}#2%
\else%
\color{MyGreen-hsb!#1!red!67!black}#2%
\fi\fi}
\newcommand{\rateA}[2]{\color{black}%
\ifnum#1=-100%
\cellcolor{red!50!black}#2%
\else\ifnum#1=100%
\cellcolor{MyGreen-hsb!50!black}#2%
\else%
\cellcolor{MyGreen-hsb!#1!red}#2%
\fi\fi}
\else
\newcommand{\rate}[2]{\ifnum#1=-100%
\color{black!25}#2%
\else\ifnum#1=100%
\color{black}#2%
\else%
\color{black!#1!white!75}#2%
\fi\fi}
\newcommand{\rateA}[2]{\color{black}%
\ifnum#1=-100%
\cellcolor{black!25}#2%
\else\ifnum#1=100%
\cellcolor{black!75}#2%
\else%
\cellcolor{black!#1!white!75}#2%
\fi\fi}
\newcommand{\TrateA}{\PrateA}
\fi
\def\Prate{\bfseries\rate}
\def\Trate{\itshape\rate}
\def\PrateA{\bfseries\rateA}
\def\TrateA{\itshape\rateA}

\newcommand*\rot{\normalsize\color{black}\rotatebox{90}}
\newcommand*\trunc{\small\truncate{12cm}}
\newcommand{\pp}[1]{\eqmakebox[pp][l]{{\color{black!50} (#1p)}}}

\setlength{\tabcolsep}{1pt}%
\setlength\extrarowheight{5pt}%
\newcolumntype{s}{>{\footnotesize\color{black!50}}c}

\begin{document}
\sffamily
\begin{tabular}{|l*{99}{|s}|}
\hline
""")


papers = {}
pc = {}
prefs= {}
prefs_type= {}
assigned = {}
email = {}

# Process preferences
with open(pref_file) as csvDataFile:
    csvReader = csv.DictReader(csvDataFile)
    for line in csvReader:
        if line['paper'] not in papers:
            papers[line['paper']] = {}
            papers[line['paper']]['title'] = line['title']
            papers[line['paper']]['n_pages'] = 20
            prefs[line['paper']] = {}
            prefs_type[line['paper']] = {}
            assigned[line['paper']] = {}
        name = line['first']+" "+line['last']
        if name not in pc:
            pc[name] = {}
            pc[name]['num'] = len(pc)
            pc[name]['email'] = line['email']
            email[line['email']] = name
            
        score = line['topic_score']
        prefs_type[line['paper']][name] = 'T'
        if line['preference']:
            score = line['preference']
            prefs_type[line['paper']][name] = 'P'
        if line['conflict'] == 'conflict':
            score = "-100"
            prefs_type[line['paper']][name] = 'C'
        prefs[line['paper']][name] = int(score)


# Process lengths
if lengths_file:
    with open(lengths_file) as csvDataFile:
        csvReader = csv.DictReader(csvDataFile)
        for line in csvReader:
            papers[line['ID']]['n_pages'] = int(line['Pages'])

# Process assignment
if assign_file:
    with open(assign_file) as csvDataFile:
        csvReader = csv.DictReader(csvDataFile)
        for line in csvReader:
            if line['action'] == "primary":
                assigned[line['paper']][email[line['email']]] = 1

# Compute individual min/max
if opt_scale:
    for name in pc:
        min = 0
        max = 0
        for p in papers:
            if name in prefs[p]:
                score = prefs[p][name]
                if score > -100:
                    if score > max:
                        max = score
                    if score < min:
                        min = score
        pc[name]['min'] = min
        pc[name]['max'] = max
else:
    for name in pc:
        pc[name]['min'] = -20
        pc[name]['max'] =  20
        
prefs_scaled = {}
for p in papers:
    prefs_scaled[p] = {}
    for name in pc:
        if name in prefs[p] and prefs[p][name] > -100:
            prefs_scaled[p][name] = int(100*(prefs[p][name]-pc[name]['min'])/(pc[name]['max']-pc[name]['min']))
            if prefs_scaled[p][name] > 100:
                prefs_scaled[p][name] = 100
            if prefs_scaled[p][name] < 0:
                prefs_scaled[p][name] = 0

if opt_order:
    # Sort papers by similarity
    sorted_papers = [ [ p ] for p in papers ]
    @functools.cache
    def paper_dist(p1, p2):
        s = 0 # sum of squares
        t = 0 # number of items
        for name in pc:
            if name in prefs_scaled[p1] and name in prefs_scaled[p2]:
                s += (prefs_scaled[p1][name]-prefs_scaled[p2][name])**2
                t += 1
        return math.sqrt(s)/math.sqrt(t)
        
    def papers_dist(l1, l2):
        p = 1
        t = 0
        for p1 in l1:
            for p2 in l2:
                p *= paper_dist(p1, p2)
                t += 1
        return p**(1/t)
    
    while len(sorted_papers) > 1:
        best = 0, 1
        for i in range(len(sorted_papers)):
            for j in range(i+1,len(sorted_papers)):
                if papers_dist(sorted_papers[i], sorted_papers[j]) < papers_dist(sorted_papers[best[0]], sorted_papers[best[1]]):
                    best = i, j
        sorted_papers = ( sorted_papers[:best[0]] +
                          [ sorted_papers[best[0]] + sorted_papers[best[1]]] +
                          sorted_papers[best[0]+1:best[1]] +
                          sorted_papers[best[1]+1:] )
    
    sorted_papers = sorted_papers[0]
    
    # Sort authors by affinity with sorted papers
    def affinity(name):
        s = 0
        t = 0
        for i in range(len(sorted_papers)):
            if name in prefs_scaled[sorted_papers[i]]:
                s += prefs_scaled[sorted_papers[i]][name]*i
                t += prefs_scaled[sorted_papers[i]][name]
        if t > 0:
            return s / t
        else:
            return -1
    sorted_pc = sorted(pc, key=affinity)
else:
    sorted_papers = papers
    sorted_pc = pc
    
# Print PC list
for name in sorted_pc:
    pages = ""
    if lengths_file:
        t = 0
        for p in papers:
            if name in assigned[p]:
                t += papers[p]['n_pages']
        pages = "\\pp{"+str(t)+"} "
    print (" & \\rot{"+pages+latex_encode(name)+"}", end='');
print ("\\\\ \\hline")

# Helper function
def pretty(p, name):
    a = "A" if name in assigned[p] else ""
    if name not in prefs[p]:
        return "\\Prate"+a+"{50}{?}"
    if prefs_type[p][name] == 'C':
        return "\\Prate"+a+"{-100}{C}"
    if prefs[p][name] == -100:
        return "\\Prate"+a+"{-100}{-100}"
    return "\\"+prefs_type[p][name]+"rate"+a+"{"+str(prefs_scaled[p][name])+"}{"+prefs_type[p][name]+str(prefs[p][name])+"}"
    
    
# Print paper scores
for p in sorted_papers:
    pages = ""
    if lengths_file:
        pages = "\\pp{"+str(papers[p]['n_pages'])+"} "
    print ("\\eqmakebox[nn][l]{"+p+".} \\trunc{"+pages+latex_encode(papers[p]['title'])+"}", end='')
    for name in sorted_pc:
        print (" & "+pretty(p,name),end='')
    print (" & "+p+" \\\\ \\hline")
    
# Print LaTeX footer
print (r"""\end{tabular}

\end{document}""")
