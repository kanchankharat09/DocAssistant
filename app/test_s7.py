# S7 test: Approve is blocked while a flag is not handled, and works after fix or dismiss.
#
# For every case with a flag in the run:
#   1. Approve without acting on the flag      -> must be blocked
#   2. Dismiss the flag, then Approve          -> must work
#   3. Fix the medicine, then Approve          -> must work
# A case without a flag must be approved at once.
#
# Run it from the main folder:   python3 app/test_s7.py            (checks results/summaries/run2)
#                                python3 app/test_s7.py run1        (another run)

import os
import sys

sys.path.insert(0, "app")
from review import fix_medicine, load_summary, open_flags, try_approve

run_name = "run2"
if len(sys.argv) > 1:
    run_name = sys.argv[1]
run_folder = "results/summaries/" + run_name
if not os.path.exists(run_folder):
    print("Folder", run_folder, "was not found.")
    sys.exit()

flagged_cases = 0
all_ok = True
for name in sorted(os.listdir(run_folder)):
    if not name.endswith(".json"):
        continue
    case_id = name[:-5]
    summary = load_summary(run_folder, case_id)
    waiting = open_flags(summary, [])

    if len(waiting) == 0:
        allowed, text = try_approve(summary, [])
        if not allowed:
            print(case_id, "FAIL  no flag but Approve is blocked")
            all_ok = False
        continue

    flagged_cases = flagged_cases + 1
    works_at_first, text = try_approve(summary, [])           # 1. nothing done yet
    dismissed = []
    for flag in waiting:
        dismissed.append(flag["key"])
    works_after_dismiss, text = try_approve(summary, dismissed)   # 2. all dismissed

    fixed = summary
    for flag in waiting:                                      # 3. fix every flagged medicine
        fixed = fix_medicine(fixed, flag["medicine_number"], "Paracetamol", "500mg")
    works_after_fix, text = try_approve(fixed, [])

    if (not works_at_first) and works_after_dismiss and works_after_fix:
        print(case_id, "pass   blocked first, works after dismiss, works after fix")
    else:
        print(case_id, "FAIL   Approve worked at first:", works_at_first, " works after dismiss:", works_after_dismiss, " works after fix:", works_after_fix)
        all_ok = False

print("cases with a flag:", flagged_cases)
if all_ok and flagged_cases > 0:
    print("S7: PASS")
else:
    print("S7: FAIL")
