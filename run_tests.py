# S11: the final run of T1 to T5 on the final build, one after the other, in one table.
#   python run_tests.py            (uses the summaries of run2)
#   python run_tests.py run2
# Warning: it runs db/seed.py first, so clinic.db is made new (visits saved with S8 are gone).
# It also adds one line to results/results_sheet.csv (the T1 scoring does that).
# It saves the table in results/final_run.txt.
#
# Pass bars (step.md):
#   T1  at least 18 of 20 summaries keep all six details
#   T2  10 of 10 planted errors flagged (and a flagged summary cannot be approved)
#   T3  20 of 20 cards for the right patient and 4 of 4 fields on all of them
#   T4  median approval time under 30 seconds, with 3 role-players
#   T5  at least 4 of the 5 code-mixed transcripts pass

import csv
import os
import subprocess
import sys
from datetime import datetime

run_name = "run2"
if len(sys.argv) > 1:
    run_name = sys.argv[1]


def run(command):
    # runs a command and returns what it printed, as a list of lines
    done = subprocess.run([sys.executable] + command, capture_output=True, text=True, encoding="utf-8")
    return (done.stdout + done.stderr).split("\n")


def find_line(lines, start):
    # the first line that starts with the given text.
    # If there is none, the command probably stopped with an error: show its last line.
    for line in lines:
        if line.startswith(start):
            return line
    last = ""
    for line in lines:
        if line.strip() != "":
            last = line
    return "(not found) last line of the output: " + last


def number_after(line, text):
    # the first whole number after the text, example: "T1 score: 16 of 20" gives 16. None if not there.
    if text not in line:
        return None
    words = line.split(text)[1].strip().split(" ")
    if words[0].isdigit():
        return int(words[0])
    return None


def median(numbers):
    ordered = sorted(numbers)
    middle = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def pass_or_fail(ok):
    if ok:
        return "Pass"
    return "Fail"


# which code is tested: look at git BEFORE we run anything, because the T1 scoring adds a line to
# results/results_sheet.csv, and that would look like an uncommitted change
commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], capture_output=True, text=True).stdout.strip()

table = []

# T1: the score of the run
t1_lines = run(["summary_service/score_t1.py", run_name])
t1_line = find_line(t1_lines, "T1 score:")
t1_score = number_after(t1_line, "T1 score:")
if t1_score is None:
    table.append("T1  summary accuracy (need 18 of 20):  NOT RUN  " + t1_line)
else:
    table.append("T1  summary accuracy (need 18 of 20):  " + str(t1_score) + " of 20   " + pass_or_fail(t1_score >= 18))

# T2: the checker (S6) and the review rule (S7)
check_lines = run(["summary_service/check_medicines.py", run_name])
flagged = number_after(find_line(check_lines, "planted errors flagged:"), "planted errors flagged:")
false_flags = number_after(find_line(check_lines, "clean cases wrongly flagged:"), "clean cases wrongly flagged:")
s7_lines = run(["app/test_s7.py", run_name])
s7_pass = find_line(s7_lines, "S7:") == "S7: PASS"
if flagged is None or false_flags is None:
    table.append("T2  medicine-dose safety:  NOT RUN  " + find_line(check_lines, "planted errors flagged:"))
else:
    table.append("T2  medicine-dose safety (need 10 of 10 flagged, at most 2 false flags, Approve blocked on a flag):  "
                 + str(flagged) + " of 10 flagged, " + str(false_flags) + " false flags, S7 test "
                 + ("pass" if s7_pass else "fail") + "   " + pass_or_fail(flagged == 10 and false_flags <= 2 and s7_pass))

# T3: the recall card (a fresh database first)
run(["db/seed.py"])
s9_lines = run(["app/test_s9.py"])
cards = number_after(find_line(s9_lines, "cards opened"), "patient:")
fields = number_after(find_line(s9_lines, "fields correct:"), "fields correct:")
if cards is None or fields is None:
    table.append("T3  recall card:  NOT RUN  " + find_line(s9_lines, "cards opened"))
else:
    table.append("T3  recall card (need 20 of 20 cards, 80 of 80 fields):  " + str(cards) + " of 20 cards, "
                 + str(fields) + " of 80 fields   " + pass_or_fail(cards == 20 and fields == 80))

# T4: the approval time of the role-play sessions (results/timing.csv)
times = []
people = []
if os.path.exists("results/timing.csv"):
    for row in csv.DictReader(open("results/timing.csv", newline="", encoding="utf-8")):
        if row["task"] == "approval" and row["correct"] == "yes":
            times.append(float(row["seconds"]))
            if row["person"] not in people:
                people.append(row["person"])
if len(people) < 3:
    table.append("T4  review time (need median under 30 s with 3 people):  NOT MEASURED  ("
                 + str(len(people)) + " people with a correct approval timing so far)")
else:
    table.append("T4  review time (need median under 30 s with 3 people):  median " + str(round(median(times), 1))
                 + " s with " + str(len(people)) + " people   " + pass_or_fail(median(times) < 30))

# T5: the code-mixed transcripts, read from the per-case lines of the T1 scoring
code_mixed = []
for row in csv.DictReader(open("test_data/MANIFEST.csv", newline="", encoding="utf-8")):
    if row["language"] == "code-mixed":
        code_mixed.append(row["id"])
passed = 0
for case_id in code_mixed:
    for line in t1_lines:
        if line.startswith(case_id + " pass"):
            passed = passed + 1
if t1_score is None:
    table.append("T5  Hindi-English (need 4 of 5):  NOT RUN")
else:
    table.append("T5  Hindi-English (need 4 of 5):  " + str(passed) + " of " + str(len(code_mixed)) + "   "
                 + pass_or_fail(passed >= 4) + "   (cases: " + ", ".join(code_mixed) + ")")

if dirty == "":
    changes = "no uncommitted changes"
else:
    changes = "WARNING: uncommitted changes, commit first and run again"

report = ["FINAL RUN OF T1 TO T5", "run: " + run_name + "   time: " + datetime.now().isoformat(timespec="seconds"),
          "git commit tested: " + commit + " (" + changes + ")", ""] + table
print("\n".join(report))
os.makedirs("results", exist_ok=True)
open("results/final_run.txt", "w", encoding="utf-8").write("\n".join(report) + "\n")
