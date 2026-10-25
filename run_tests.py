# S10: runs T1, T2 and T3 on the final build, one after the other, and prints the numbers.
#   python run_tests.py            (uses the summaries of run2)
#   python run_tests.py run2
# Warning: it runs db/seed.py first, so clinic.db is made new (visits saved with S8 are gone).
# It also adds one line to results/results_sheet.csv (the T1 scoring does that).

import subprocess
import sys

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


print("T1 (summary accuracy, need 18 of 20)")
print("   ", find_line(run(["summary_service/score_t1.py", run_name]), "T1 score:"))

print("T2 (medicine and dose checker, need 10 of 10 and at most 2 false flags)")
lines = run(["summary_service/check_medicines.py", run_name])
print("   ", find_line(lines, "planted errors flagged:"))
print("   ", find_line(lines, "clean cases wrongly flagged:"))
print("   ", find_line(lines, "S6:"))

print("T3 (recall card, need 20 of 20 cards and every field correct)")
run(["db/seed.py"])
lines = run(["app/test_s9.py"])
print("   ", find_line(lines, "cards opened"))
print("   ", find_line(lines, "fields correct:"))
print("   ", find_line(lines, "S9:"))
