# S10: replaces the 3 approval timings (R3 3.0 s, R2 4.3 s, R2 2.7 s) that are measured again.
#   python replace_fast_rows.py
# Run it AFTER the 3 new timings are saved on the Timing page.
# It removes the 3 old rows from results/timing.csv (the file is changed in place, no new file).
# The old rows stay in the git history. If a new row is missing, it stops and changes nothing.

import csv

timing_file = "results/timing.csv"

# the old rows: (person, task, patient) and the patient who replaces it
old_rows = [("R3", "approval", "Vikram Singh"), ("R2", "approval", "Rajesh Kale"),
            ("R2", "approval", "Meera Iyer")]
new_patients = [("R3", "approval", "Kishan Lal"), ("R2", "approval", "Ramesh Kulkarni"),
                ("R2", "approval", "Arjun Patil")]

rows = list(csv.DictReader(open(timing_file, newline="", encoding="utf-8")))


def has_row(person, task, patient):
    for row in rows:
        if row["person"] == person and row["task"] == task and row["patient"] == patient:
            return True
    return False


missing = []
for person, task, patient in new_patients:
    # the new timing must be after the old one: look for a row that is not an old row
    if not has_row(person, task, patient):
        missing.append(person + " " + task + " " + patient)
if missing:
    print("Stopped, nothing changed. These new timings are not saved yet: " + ", ".join(missing))
    raise SystemExit(1)

kept = []
removed = 0
for row in rows:
    if (row["person"], row["task"], row["patient"]) in old_rows:
        removed = removed + 1
    else:
        kept.append(row)

with open(timing_file, "w", newline="", encoding="utf-8") as out:
    writer = csv.DictWriter(out, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(kept)
print("Removed " + str(removed) + " old rows, " + str(len(kept)) + " rows kept.")
