# S8 test: approve 15 of the 20 summaries and leave 5 unapproved. Then check:
#   - 15 visits are saved
#   - 0 of the unapproved summaries are saved
#   - the audit log has 20 of 20 entries (one for each summary), each with a time and an action
# The doctor handles the flags before Approve: here the test dismisses every flag.
#
# Run it from the main folder:
#   python3 db/seed.py          (a fresh database)
#   python3 app/test_s8.py      (uses results/summaries/run2, or give another run name)

import os
import sqlite3
import sys

sys.path.insert(0, "app")
from review import load_summary, open_flags
from save import approve_and_save, leave_unapproved, new_visit_id

run_name = "run2"
if len(sys.argv) > 1:
    run_name = sys.argv[1]
run_folder = "results/summaries/" + run_name
if not os.path.exists(run_folder) or not os.path.exists("clinic.db"):
    print("Missing", run_folder, "or clinic.db. Run db/seed.py first.")
    sys.exit()

case_ids = []
for name in sorted(os.listdir(run_folder)):
    if name.endswith(".json"):
        case_ids.append(name[:-5])

approved_cases = []
left_cases = []
for number in range(len(case_ids)):
    case_id = case_ids[number]
    if number < 15:                       # the first 15 are approved
        summary = load_summary(run_folder, case_id)
        dismissed = []
        for flag in open_flags(summary, []):
            dismissed.append(flag["key"])
        approve_and_save(case_id, summary, dismissed)
        approved_cases.append(case_id)
    else:                                 # the last 5 are left unapproved
        leave_unapproved(case_id)
        left_cases.append(case_id)

con = sqlite3.connect("clinic.db")
saved_ids = []
for (visit_id,) in con.execute("SELECT visit_id FROM visits WHERE approved = 1 AND visit_id LIKE 'NV%'"):
    saved_ids.append(visit_id)

saved_ok = 0
for case_id in approved_cases:
    if new_visit_id(case_id) in saved_ids:
        saved_ok = saved_ok + 1
unapproved_saved = 0
for case_id in left_cases:
    if new_visit_id(case_id) in saved_ids:
        unapproved_saved = unapproved_saved + 1

audit_ok = 0
for case_id in approved_cases + left_cases:
    rows = con.execute("SELECT time, action FROM audit_log WHERE visit_id = ?", (new_visit_id(case_id),)).fetchall()
    if len(rows) == 1 and rows[0][0] != "" and rows[0][1] != "":
        audit_ok = audit_ok + 1
con.close()

print("approved and saved:", saved_ok, "of", len(approved_cases), "(need 15)")
print("unapproved but saved:", unapproved_saved, "(need 0)")
print("audit log entries with time and action:", audit_ok, "of", len(case_ids), "(need 20)")
if len(case_ids) == 20 and saved_ok == 15 and unapproved_saved == 0 and audit_ok == 20:
    print("S8: PASS")
else:
    print("S8: FAIL")
