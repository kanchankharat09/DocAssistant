# S2: make a small database with fake patients and one old visit for each.
# The old visit comes from the expected summary of each transcript.
# Run it from the main folder:  python3 db/seed.py

import os
import sqlite3
from datetime import datetime, timedelta

# folders and file names
test_data_folder = "test_data"
db_file = "clinic.db"

# delete the old database so we always start from empty
if os.path.exists(db_file):
    os.remove(db_file)

con = sqlite3.connect(db_file)

# make the 4 tables
con.execute("CREATE TABLE patients (patient_id TEXT, name TEXT, age INTEGER, sex TEXT)")
con.execute("CREATE TABLE visits (visit_id TEXT, patient_id TEXT, visit_date TEXT, main_complaint TEXT, medicines TEXT, follow_up_advice TEXT, approved INTEGER)")
con.execute("CREATE TABLE summaries (summary_id TEXT, visit_id TEXT, text TEXT)")
con.execute("CREATE TABLE audit_log (time TEXT, action TEXT, visit_id TEXT)")

# get all the expected summary files, sorted so the order is always same
files = []
for name in os.listdir(test_data_folder):
    if name.endswith("_expected_summary.txt"):
        files.append(name)
files.sort()

number = 0
for file_name in files:
    number = number + 1
    text = open(test_data_folder + "/" + file_name).read()

    # read the lines we need from the summary
    patient_line = ""
    date_line = ""
    complaint = ""
    advice = ""
    medicines = ""
    in_medicines = False

    for line in text.split("\n"):
        if line.startswith("Patient:"):
            patient_line = line.replace("Patient:", "").strip()   # example: Ramesh Kulkarni, 58M
        elif line.startswith("Date:"):
            date_line = line.replace("Date:", "").strip()
        elif line.startswith("Chief complaint:"):
            complaint = line.replace("Chief complaint:", "").strip()
        elif line.startswith("Doctor instructions:"):
            advice = line.replace("Doctor instructions:", "").strip()
        elif line.startswith("Medicines prescribed:"):
            in_medicines = True
        elif in_medicines and line.startswith("- "):
            medicines = medicines + line[2:] + "\n"
        else:
            in_medicines = False

    # split "Ramesh Kulkarni, 58M" into name, age and sex
    name_part, age_sex = patient_line.split(",")
    age_sex = age_sex.strip()
    age = int(age_sex[:-1])
    sex = age_sex[-1]

    # old visit is 21 days before the transcript date
    transcript_date = datetime.strptime(date_line, "%d %b %Y")
    old_date = (transcript_date - timedelta(days=21)).strftime("%Y-%m-%d")

    patient_id = "P" + str(number).zfill(2)
    visit_id = "V" + str(number).zfill(2)
    summary_id = "S" + str(number).zfill(2)

    con.execute("INSERT INTO patients VALUES (?, ?, ?, ?)", (patient_id, name_part.strip(), age, sex))
    con.execute("INSERT INTO visits VALUES (?, ?, ?, ?, ?, ?, 1)", (visit_id, patient_id, old_date, complaint, medicines.strip(), advice))
    con.execute("INSERT INTO summaries VALUES (?, ?, ?)", (summary_id, visit_id, text))
    con.execute("INSERT INTO audit_log VALUES (?, ?, ?)", (datetime.now().isoformat(), "seeded old visit", visit_id))

con.commit()

# check: how many rows did we make
patients_count = con.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
visits_count = con.execute("SELECT COUNT(*) FROM visits").fetchone()[0]
print("patients:", patients_count, " visits:", visits_count)
