# S7: the logic behind the review screen.
# It loads an AI summary, finds the flags with the medicine checker of S6, and decides
# if the doctor can press Approve. The screen (app/pages/1_Review.py) uses these functions
# and app/test_s7.py tests them.
#
# A flag is "handled" in one of two ways:
#   - dismissed: the doctor says "this is fine" (we keep the flag text in a list called dismissed)
#   - fixed: the doctor changes the medicine name or dose, so the checker does not flag it any more
# Approve is blocked while there is a flag that is not handled.
# Saving the approved visit comes in S8.

import copy
import json
import sys

sys.path.insert(0, "summary_service")
from check_medicines import check_medicine, read_formulary


def load_summary(run_folder, case_id):
    # reads the AI summary of one case, example: results/summaries/run2/T02.json
    file_name = run_folder + "/" + case_id + ".json"
    return json.loads(open(file_name, encoding="utf-8").read())["summary"]


def find_flags(summary):
    # checks every medicine of the summary and returns a list of flags
    formulary = read_formulary()
    flags = []
    medicines = summary.get("medicines", [])
    for number in range(len(medicines)):
        message = check_medicine(medicines[number]["name"], medicines[number]["dose"], formulary)
        if message != "":
            # the key says which medicine and why; the doctor's "dismiss" is remembered with this key
            flags.append({"key": str(number) + ": " + message, "medicine_number": number, "message": message})
    return flags


def open_flags(summary, dismissed):
    # the flags that are not handled yet: flagged now and not dismissed by the doctor
    still_open = []
    for flag in find_flags(summary):
        if flag["key"] not in dismissed:
            still_open.append(flag)
    return still_open


def fix_medicine(summary, medicine_number, new_name, new_dose):
    # returns a new summary with the medicine name and dose changed by the doctor
    fixed = copy.deepcopy(summary)
    fixed["medicines"][medicine_number]["name"] = new_name
    fixed["medicines"][medicine_number]["dose"] = new_dose
    return fixed


def try_approve(summary, dismissed):
    # returns (True, text) if Approve works, or (False, text) if it is blocked
    waiting = open_flags(summary, dismissed)
    if len(waiting) > 0:
        return False, "Blocked: " + str(len(waiting)) + " flag(s) not handled yet. Fix or dismiss them first."
    return True, "Approved."
