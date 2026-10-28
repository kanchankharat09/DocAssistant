# S10: removes the 4 rows that are not part of the plan (found when the 48 saved timings were checked).
#   python remove_extra_rows.py
# The file results/timing.csv is changed in place. The removed rows stay in the git history.
# If one of the rows is not found, it stops and changes nothing.

import csv

timing_file = "results/timing.csv"

# (time of the row, why it is removed)
extra_rows = [
    ("2026-10-28T22:37:03", "R1 transcript Kishan Lal 17.9 s: second read of the same patient (practice)"),
    ("2026-10-28T22:38:40", "R1 transcript Vikram Singh 15.5 s: second read of the same patient (practice)"),
    ("2026-10-28T22:39:43", "R1 transcript Sunita Deshmukh 19.4 s: not planned, R1 had timed this patient as a card"),
    ("2026-10-28T22:14:35", "R3 card Sunita Verma 7.8 s: the practice patient of R3"),
]

rows = list(csv.DictReader(open(timing_file, newline="", encoding="utf-8")))
times = [row["time"] for row in rows]
missing = [when for when, why in extra_rows if when not in times]
if missing:
    print("Stopped, nothing changed. These rows are not found: " + ", ".join(missing))
    raise SystemExit(1)

drop = [when for when, why in extra_rows]
kept = [row for row in rows if row["time"] not in drop]
with open(timing_file, "w", newline="", encoding="utf-8") as out:
    writer = csv.DictWriter(out, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(kept)
for when, why in extra_rows:
    print("removed: " + why)
print(str(len(rows) - len(kept)) + " rows removed, " + str(len(kept)) + " rows kept.")
