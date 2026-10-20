"""S2: build clinic.db with fictional patients and one prior approved visit each.

Each patient comes from a transcript's expected summary (option B): the expected
summary becomes the prior visit, dated 21 days before the transcript date.

Usage (from repo root):  python3 db/seed.py
"""
import datetime, pathlib, re, sqlite3

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEST_DATA = ROOT / "test_data"
DB = ROOT / "clinic.db"

SCHEMA = """
CREATE TABLE patients (patient_id TEXT PRIMARY KEY, name TEXT, age INTEGER, sex TEXT);
CREATE TABLE visits (visit_id TEXT PRIMARY KEY, patient_id TEXT, visit_date TEXT,
    main_complaint TEXT, medicines TEXT, follow_up_advice TEXT, approved INTEGER);
CREATE TABLE summaries (summary_id TEXT PRIMARY KEY, visit_id TEXT, text TEXT);
CREATE TABLE audit_log (log_id INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT, action TEXT, visit_id TEXT);
"""


def field(text, label):
    m = re.search(rf"^{label}:\s*(.*)$", text, re.M)
    return m.group(1).strip() if m else ""


def medicines(text):
    block = text.split("Medicines prescribed:")[1].split("\n\n")[0]
    return "\n".join(l[2:].strip() for l in block.strip().splitlines() if l.startswith("- "))


def main():
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA)
    for i, f in enumerate(sorted(TEST_DATA.glob("T??_expected_summary.txt")), start=1):
        text = f.read_text()
        name, rest = field(text, "Patient").split(",", 1)
        age, sex = int(re.search(r"\d+", rest).group()), rest.strip()[-1]
        d = datetime.datetime.strptime(field(text, "Date"), "%d %b %Y").date()
        pid, vid = f"P{i:02d}", f"V{i:02d}"
        con.execute("INSERT INTO patients VALUES (?,?,?,?)", (pid, name.strip(), age, sex))
        con.execute("INSERT INTO visits VALUES (?,?,?,?,?,?,1)", (
            vid, pid, (d - datetime.timedelta(days=21)).isoformat(),
            field(text, "Chief complaint"), medicines(text), field(text, "Doctor instructions")))
        con.execute("INSERT INTO summaries VALUES (?,?,?)", (f"S{i:02d}", vid, text))
        con.execute("INSERT INTO audit_log (time, action, visit_id) VALUES (?,?,?)",
                    (datetime.datetime.now().isoformat(timespec="seconds"), "seeded prior visit", vid))
    con.commit()
    n_p = con.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
    n_v = con.execute("SELECT COUNT(*) FROM visits").fetchone()[0]
    phones = sum(1 for (t,) in con.execute("SELECT name || age FROM patients") if re.search(r"\d{7,}", t))
    print(f"patients: {n_p}   visits: {n_v}   rows with a phone-like number: {phones}")


if __name__ == "__main__":
    main()
