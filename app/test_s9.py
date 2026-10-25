# S9 test: search each of the 20 patients by name and check the recall card.
#   - the card must open for the right patient (20 of 20)
#   - the 4 fields must be correct on every card (4 of 4)
# The right answers are read again from the expected summaries (not from the database),
# the old visit is 21 days before the date written there, as in db/seed.py.
#
# Run it:   python3 db/seed.py        (once, to make clinic.db)
#           python3 app/test_s9.py

import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, "app")
from recall import find_patients, get_recall_card

test_data_folder = "test_data"


def read_expected(file_name):
    # reads name, date, complaint, medicines and advice from an expected summary
    answer = {"name": "", "visit_date": "", "main_complaint": "", "medicines": "", "follow_up_advice": ""}
    medicines = []
    in_medicines = False
    for line in open(file_name, encoding="utf-8").read().split("\n"):
        if line.startswith("Patient:"):
            answer["name"] = line.replace("Patient:", "").split(",")[0].strip()
        elif line.startswith("Date:"):
            date = datetime.strptime(line.replace("Date:", "").strip(), "%d %b %Y")
            answer["visit_date"] = (date - timedelta(days=21)).strftime("%Y-%m-%d")
        elif line.startswith("Chief complaint:"):
            answer["main_complaint"] = line.replace("Chief complaint:", "").strip()
        elif line.startswith("Doctor instructions:"):
            answer["follow_up_advice"] = line.replace("Doctor instructions:", "").strip()
        if line.startswith("Medicines prescribed:"):
            in_medicines = True
        elif in_medicines and line.startswith("- "):
            medicines.append(line[2:])
        else:
            in_medicines = False
    answer["medicines"] = "\n".join(medicines)
    return answer


cards_ok = 0
fields_ok = 0
total = 0
for name in sorted(os.listdir(test_data_folder)):
    if not name.endswith("_expected_summary.txt"):
        continue
    total = total + 1
    expected = read_expected(test_data_folder + "/" + name)

    # search by the full name; the right patient must be the only one found
    found = find_patients(expected["name"])
    card = None
    if len(found) == 1 and found[0]["name"] == expected["name"]:
        card = get_recall_card(found[0]["patient_id"])
    if card is None or card["name"] != expected["name"]:
        print(name[:3], "FAIL  card did not open for", expected["name"], "(found", len(found), "patients)")
        continue
    cards_ok = cards_ok + 1

    wrong_fields = []
    for field in ["visit_date", "main_complaint", "medicines", "follow_up_advice"]:
        if card[field] == expected[field]:
            fields_ok = fields_ok + 1
        else:
            wrong_fields.append(field)
    if len(wrong_fields) == 0:
        print(name[:3], "pass ", expected["name"])
    else:
        print(name[:3], "FAIL  wrong fields:", wrong_fields)

print("cards opened for the right patient:", cards_ok, "of", total, "(need all)")
print("fields correct:", fields_ok, "of", total * 4, "(need all, 4 of 4 on every card)")
if total == 20 and cards_ok == 20 and fields_ok == 80:
    print("S9: PASS")
else:
    print("S9: FAIL")
