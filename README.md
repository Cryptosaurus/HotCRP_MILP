# HotCRP_MILP

This repository contains simple scripts to do paper assignment for HotCRP using a MILP solver.
The scripts are not used inside HotCRP, but externally, using the import/export functionality of HotCRP.

There are two programs:
- `assign_milp` does the assignment itself; it requires at least SAGE 9.0.
- `assign_matrix` is used to visualize the assignement (it outputs a LaTeX file)
The idea is that both programs are quite simple, so they can be tweaked manually if they don't do what is needed.

They have been developped for ToSC, and also used for Eurocrypt.

## assign_milp

The basic functionality is to select an assignment that maximizes the sum of preference scores, with all reviewers having the same number of papers (±1).

There are several options to further constraint the assignment (keep the total number of reviewed pages roughly the same, have at least one reviewer that really wants the paper, ...).  It was very useful for ToSC, but the MILP solver might struggle for conferences with a larger number of papers and reviewers.

You can also easily do some manual tweaks to the MILP program before solving it (eg. assign paper X to reviewer Y, assign fewer papers to reviews Z, assign more reviewers to PC papers, etc.).

There is an option to take into account the number of pages of each paper, but you need to generate this information somehow (either by hand, or by adding a field in the submission form).

*Important note:*

You should explain to the reviewers that the assignment does not follow exactly the rules explained by HotCRP.  The score are taken as the manual score if it exists, or the topic_score (automatically computed from each reviewers topic preferences) if no manual score was entered.

If a reviewer uses both types of scores, he should make sure the scales are the same.  You must also make sure that reviewers do not use the manual grade 0, because there is no way to distinguish a true grade of zero and an unset grade (resulting in the topic score being used).

The program has an option to scale grades automatically based on each reviewers min and max grade, you should use it if the grades are not uniform (eg one reviewer grading between 0 and 10, and another between -20 and 20).


## assign_matrix

There is an option to group similar papers and reviewrs, and order them so that most of the selected papers are along the diagonal.  This is quite useful to modify the assignment manually, but I don't know if it scales well to a large conference (it probably take quadratic or cubic time).
