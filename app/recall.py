# S9: look up a patient by name and build the recall card of the last approved visit.
# The card has 4 fields: visit date, main complaint, medicines with doses, follow-up advice.
# The screen (app/app.py) uses these two functions, and app/test_s9.py tests them.

import sqlite3

db_file = "clinic.db"


def find_patients(search_text):
    # returns the patients whose name has the search text in it (small or capital letters, same)
    con = sqlite3.connect(db_file)
    patients = []
    rows = con.execute("SELECT patient_id, name, age, sex FROM patients ORDER BY name").fetchall()
    for patient_id, name, age, sex in rows:
        if search_text.strip().lower() in name.lower():
            patients.append({"patient_id": patient_id, "name": name, "age": age, "sex": sex})
    con.close()
    return patients


def get_recall_card(patient_id):
    # returns the card of the last approved visit of this patient, or None if there is none
    con = sqlite3.connect(db_file)
    patient = con.execute("SELECT name, age, sex FROM patients WHERE patient_id = ?", (patient_id,)).fetchone()
    visit = con.execute(
        "SELECT visit_date, main_complaint, medicines, follow_up_advice FROM visits "
        "WHERE patient_id = ? AND approved = 1 ORDER BY visit_date DESC LIMIT 1", (patient_id,)).fetchone()
    con.close()
    if patient is None or visit is None:
        return None
    return {
        "name": patient[0], "age": patient[1], "sex": patient[2],
        "visit_date": visit[0],
        "main_complaint": visit[1],
        "medicines": visit[2],
        "follow_up_advice": visit[3],
    }
