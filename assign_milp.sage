#! /usr/bin/env sage
# coding=utf-8

# This script uses a MILP solver to assign reviewers from HotCRP review preferences
#
# Usage:
# sage assign_milp.pl allprefs.csv
# Output is in pcassignments.csv.  Can be uploaded to HotCRP.

# CSV file can be downloaded by selecting all papers, clicking download
# and selecting "PC review preferences"
# If there is a 'Pages' field in the sumbission form, a CSV file with paper
# lengths can be download using the "CSV" option under download
# NOTE: adding constraints on the number of pages per reviewer with -l and -r
# makes the MILP problem much harder to solve!

def usage():
    print("Usage: {} allprefs.csv [-s] [-n] [-m0.8] [-l data.csv] [-r1.3]".format(sys.argv[0]))    
    print("\nOptions:")
    print("  -s  or --scale: autoscale preferences according to individual min/max (otherwise assume -20/20)")
    print("  -n  or --noneg: don't assign reviewers with negative scores")
    print("  -mX or --minscore X: each paper must have one reviewer with relative score X (between 0 and 1). Default: 0.8")
    print("  -l or --lengths: read paper lengths from CSV file")
    print("  -rX or --ratio X: each reviewer has at most X times the average number of pages to review.  Default: 1.5")

import csv
import itertools
import getopt, sys

try:
    opts, args = getopt.gnu_getopt(sys.argv[1:], "sm:nl:r:", ["scale", "minscore=", "noneg", "lengths=", "ratio="])
except getopt.GetoptError as err:
    # print help information and exit:
    print(err)  # will print something like "option -a not recognized"
    usage()
    sys.exit(2)


pref_file = None
lengths_file = None
opt_scale = 0
opt_noneg = 0
opt_minscore = 0.8
opt_ratio = 1.5

for o, a in opts:
    if o in ("-s", "--scale"):
        opt_scale = 1
    elif o in ("-m", "--minscore"):
        opt_minscore = N(a)
    elif o in ("-n", "--noneg"):
        opt_noneg = 1
    elif o in ("-l", "--lengths"):
        lengths_file = a
    elif o in ("-r", "--ratio"):
        opt_ratio = N(a)
    else:
        assert False, "unhandled option"

if len(args) == 1:
    pref_file = args[0]
else:
    print ("Error: wrong number of arguments")
    usage()
    sys.exit(2)

papers = {}
pc = {}
prefs= {}

# Process preferences
with open(pref_file) as csvDataFile:
    csvReader = csv.DictReader(csvDataFile)
    for line in csvReader:
        if line['paper'] not in papers:
            papers[line['paper']] = {}
            papers[line['paper']]['title'] = line['title']
            papers[line['paper']]['n_rev'] = 3
            papers[line['paper']]['n_pages'] = 20
            prefs[line['paper']] = {}
        name = line['first']+" "+line['last']
        if name not in pc:
            pc[name] = {}
            pc[name]['num'] = len(pc)
            pc[name]['email'] = line['email']
            
        score = line['topic_score']
        if line['preference']:
            score = line['preference']
        if line['conflict'] == 'conflict':
            score = "-100"
        prefs[line['paper']][name] = int(score)

# Process lengths
if lengths_file:
    with open(lengths_file) as csvDataFile:
        csvReader = csv.DictReader(csvDataFile)
        for line in csvReader:
            papers[line['ID']]['n_pages'] = int(line['Pages'])

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

# MANUAL TWEAKS
# You can adjust the matrix before doing the assignment.  Exemples below:

# ## Remove chairs
# del pc['Gaëtan Leurent']

# ## Remove out-of-scope papers
# del papers['42']

# ## PC-authored papers
# for p in [ '1', '2', '42']:
#     papers[p]['n_rev'] = 4

# Build MILP program
milp = MixedIntegerLinearProgram(maximization=True)
sel = milp.new_variable(binary=True, indices=itertools.product(papers,pc))


# ## Manually assign some papers
# milp.add_constraint(sel['1', 'Alice Crypto'], min = 1)

# ## Major revisions
# milp.add_constraint(sel['42', 'Bob Reviewer'], min = 1)



prefs_scaled = {}
for p in papers:
    prefs_scaled[p] = {}
    for name in pc:
        if name in prefs[p] and prefs[p][name] > -100:
            prefs_scaled[p][name] = N((prefs[p][name]-pc[name]['min'])/(pc[name]['max']-pc[name]['min']))
            if prefs_scaled[p][name] > 1:
                prefs_scaled[p][name] = 1
            if prefs_scaled[p][name] < 0:
                prefs_scaled[p][name] = 0
        
# Objective function
obj = 0
for name in pc:
    for p in papers:
        if name in prefs_scaled[p]:
            obj = obj + sel[p,name]*(prefs_scaled[p][name])
milp.set_objective(obj)

# Constraints
## Conflicts
for p in papers:
    for name in pc:
        if name in prefs[p] and prefs[p][name] <= -100:
            milp.add_constraint(sel[p,name], max = 0)

## Review per papers
for p in papers:
    n = 0
    for name in pc:
        n = n + sel[p,name]
    milp.add_constraint(n, min = papers[p]['n_rev'])
    milp.add_constraint(n, max = papers[p]['n_rev'])

## Average number of reviews
n_rev_min = floor(sum(papers[p]['n_rev'] for p in papers)/len(pc))
n_rev_max = ceil(sum(papers[p]['n_rev'] for p in papers)/len(pc))
for name in pc:
    n = 0
    for p in papers:
        n = n + sel[p,name]
    milp.add_constraint(n, min = n_rev_min)
    milp.add_constraint(n, max = n_rev_max)

if lengths_file:
    ## Average page load
    n_pages_avg = int(sum(papers[p]['n_pages']*papers[p]['n_rev'] for p in papers)/len(pc))
    for name in pc:
        n = 0
        for p in papers:
            n = n + sel[p,name]*int(papers[p]['n_pages'])
        milp.add_constraint(n, min = int(n_pages_avg/opt_ratio))
        milp.add_constraint(n, max = int(n_pages_avg*opt_ratio))

## At least one reviewer wants the paper
if opt_minscore:
    for p in papers:
        n = 0
        for name in pc:
            if name in prefs_scaled[p] and prefs_scaled[p][name] > opt_minscore:
                n = n + sel[p,name]
        if type(n) == type(0):
            print ("Nobody wants "+p)
        else:
            milp.add_constraint(n, min = 1)

## All scores must be positive
if opt_noneg:
    ## No negative score
    for p in papers:
        for name in pc:
            if name not in prefs[p] or prefs[p][name] <= 0:
                milp.add_constraint(sel[p,name], max = 0)

milp.solve()
sol = milp.get_values(sel)
# for x in sol:
#     if sol[x]:
#         print(x)
        
with open('pcassignments.csv', 'w') as f:
    f.write("paper,action,email,title\n")
    for p,name in sol:
        if sol[p,name]:
            f.write("{},primary,{}\n".format(p, pc[name]['email']))
        
print ("Assignment written to pcassignments.csv")
