# S10: replaces the 4 card timings that were too fast to be a real attempt (under 2.5 s).
#   python replace_fast_rows.py
# Run it AFTER the 4 new timings are saved on the Timing page.
# It first saves the old file as results/timing_round1_backup.csv, then removes the 4 old rows
# and does not touch anything else. If a new row is missing, it stops and changes nothing.

import csv
import os
import shutil

timing_file = "results/timing.csv"
backup_file = "results/timing_round1_backup.csv"

# the old rows: (person, task, patient) and the patient who replaces it
old_rows = [("R2", "card", "Meena Pawar"), ("R3", "card", "Anita Bhosale"),
            ("R3", "card", "Sanjay More"), ("R3", "card", "Imran Sheikh")]
new_patients = [("R2", "card", "Sunita Verma"), ("R3", "card", "Rohan Mehta"),
                ("R3", "card", "Ramesh Kulkarni"), ("R3", "card", "Arjun Patil")]

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

shutil.copy(timing_file, backup_file)
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
print("Old file saved as " + backup_file + ". Removed " + str(removed) + " old rows, " + str(len(kept)) + " rows kept.")
