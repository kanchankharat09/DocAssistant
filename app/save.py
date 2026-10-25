# S8: approve and save a visit, and write every action in the audit log.
#
# Rule of the plan: nothing is saved until the doctor approves.
#   - Approve works only when every flag is fixed or dismissed (the rule of S7)
#   - on Approve the visit is saved in the table "visits" (approved = 1) and in "summaries"
#   - a summary that is left unapproved is NOT saved, but the audit log says so
#   - every action goes in the table "audit_log" with the time, the action and the visit id
# The screen (app/pages/1_Review.py) uses these functions and app/test_s8.py tests them.

import json
import sqlite3
import sys
from datetime import datetime

sys.path.insert(0, "app")
from review import try_approve

db_file = "clinic.db"
test_data_folder = "test_data"


def write_audit(con, action, visit_id):
    # one line in the audit log: time, action, visit id
    con.execute("INSERT INTO audit_log VALUES (?, ?, ?)", (datetime.now().isoformat(), action, visit_id))


def patient_id_of(case_id):
    # one patient per transcript (see db/seed.py): T05 is the patient P05
    return "P" + case_id[1:]


def new_visit_id(case_id):
    # the id of the visit made from this transcript: T05 gives NV05
    return "NV" + case_id[1:]


def transcript_date(case_id):
    # reads "Date: 15 Oct 2026" from the first lines of the transcript and returns 2026-10-15
    for line in open(test_data_folder + "/" + case_id + "_transcript.txt", encoding="utf-8").read().split("\n"):
        if line.startswith("Date:"):
            date = datetime.strptime(line.replace("Date:", "").strip(), "%d %b %Y")
            return date.strftime("%Y-%m-%d")
    return ""


def medicines_text(summary):
    # one line for each medicine, like  Paracetamol 500mg — three times a day — 3 days
    lines = []
    for medicine in summary.get("medicines", []):
        line = (medicine["name"] + " " + medicine["dose"]).strip()
        if medicine.get("frequency", "") != "":
            line = line + " — " + medicine["frequency"]
        if medicine.get("duration", "") != "":
            line = line + " — " + medicine["duration"]
        lines.append(line)
    return "\n".join(lines)


def approve_and_save(case_id, summary, dismissed):
    # returns (True, text) when the visit is saved, (False, text) when it is blocked
    con = sqlite3.connect(db_file)
    visit_id = new_visit_id(case_id)

    allowed, text = try_approve(summary, dismissed)
    if not allowed:
        write_audit(con, "approve blocked", visit_id)
        con.commit()
        con.close()
        return False, text

    already = con.execute("SELECT COUNT(*) FROM visits WHERE visit_id = ?", (visit_id,)).fetchone()[0]
    if already > 0:
        con.close()
        return False, "This visit is already saved."

    con.execute("INSERT INTO visits VALUES (?, ?, ?, ?, ?, ?, 1)",
                (visit_id, patient_id_of(case_id), transcript_date(case_id),
                 summary.get("chief_complaint", ""), medicines_text(summary),
                 summary.get("doctor_instructions", "")))
    con.execute("INSERT INTO summaries VALUES (?, ?, ?)",
                ("S" + case_id[1:] + "N", visit_id, json.dumps(summary, indent=2, ensure_ascii=False)))
    write_audit(con, "approved and saved", visit_id)
    con.commit()
    con.close()
    return True, "Approved and saved."


def leave_unapproved(case_id):
    # the doctor does not approve: nothing is saved, only the audit log gets a line
    con = sqlite3.connect(db_file)
    write_audit(con, "left unapproved", new_visit_id(case_id))
    con.commit()
    con.close()
