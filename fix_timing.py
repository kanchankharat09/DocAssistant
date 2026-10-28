# S10: removes the timing rows that were recorded by mistake, and makes the database new.
#   python fix_timing.py
# It removes only these rows of results/timing.csv (you told me the reasons):
#   1. the second set of R1 card timings (recorded at 09:59 and 10:00 on 28 Oct): the first set is kept,
#      because R1 recorded the same three cards twice and the second set was interrupted by chat
#   2. the R1 approval of Ramesh Kulkarni of 47.3 s: it was interrupted by chat, so R1 measures it again
# It makes a backup first (results/timing_before_fix.csv) and prints every row it removes.
# Then it runs db/seed.py so that T04 can be approved again (otherwise: "This visit is already saved.").

import csv
import os
import shutil
import subprocess
import sys

sys.path.insert(0, "app")
from timing import make_report

timing_file = "results/timing.csv"
backup_file = "results/timing_before_fix.csv"

if not os.path.exists(timing_file):
    print(timing_file, "was not found.")
    sys.exit()

shutil.copy(timing_file, backup_file)
rows = list(csv.reader(open(timing_file, newline="", encoding="utf-8")))
header = rows[0]
data = rows[1:]

keep = []
for row in data:
    time, person, task, patient, seconds = row[0], row[1], row[2], row[3], row[4]
    second_set = person == "R1" and task == "card" and (time.startswith("2026-10-28T09:59") or time.startswith("2026-10-28T10:00"))
    interrupted_approval = person == "R1" and task == "approval" and patient == "Ramesh Kulkarni" and seconds == "47.3"
    if second_set or interrupted_approval:
        print("removed:", ",".join(row))
    else:
        keep.append(row)

out_file = open(timing_file, "w", newline="", encoding="utf-8")
writer = csv.writer(out_file, lineterminator="\n")
writer.writerow(header)
writer.writerows(keep)
out_file.close()
print(len(data), "rows before,", len(keep), "rows now. Backup:", backup_file)

# the report of the rows that are left
rows_left = []
for row in keep:
    rows_left.append({"time": row[0], "person": row[1], "task": row[2], "patient": row[3], "seconds": float(row[4]), "correct": row[5]})
report = make_report(rows_left)
print("card timings now:", report["card_count"], "| people:", len(report["people"]))

# a fresh database (db/seed.py makes it new each time)
done = subprocess.run([sys.executable, "db/seed.py"], capture_output=True, text=True, encoding="utf-8")
if done.returncode == 0:
    print("database made new: T04 can be approved again.")
else:
    print("could not make the database new:", done.stderr.strip().split("\n")[-1])
    print("Stop Streamlit (Ctrl+C) and run:  python db/seed.py")

print("")
print("Now measure again, without any chat in between:")
print("  Timing page: label R1, task approval, patient Ramesh Kulkarni")
print("  Review page: case T04. Start on the Timing page, handle the flag, Approve and save, Stop, yes, Save.")
