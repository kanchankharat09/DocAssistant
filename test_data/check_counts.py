"""Count S1 deliverables. Run from repo root: python3 test_data/check_counts.py"""
import csv, pathlib

d = pathlib.Path(__file__).parent
tr = sorted(p.stem[:3] for p in d.glob("T??_transcript.txt"))
ex = sorted(p.stem[:3] for p in d.glob("T??_expected_summary.txt"))
rows = list(csv.DictReader(open(d / "MANIFEST.csv")))
cm = [r["id"] for r in rows if r["language"] == "code-mixed"]
pe = [r["id"] + ":" + r["planted_error"] for r in rows if r["planted_error"] != "none"]
print(f"transcripts: {len(tr)}/20   expected summaries: {len(ex)}/20")
print(f"code-mixed (planned): {len(cm)}/5   planted errors (planned): {len(pe)}/10")
print("missing transcript:", sorted({r['id'] for r in rows} - set(tr)))
print("missing summary:   ", sorted({r['id'] for r in rows} - set(ex)))
print("planted:", ", ".join(pe))
