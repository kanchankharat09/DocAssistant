# S1 count script: counts the files in test_data and prints what is still missing.
# Run it from the main folder:  python3 test_data/check_counts.py

import csv
import os

folder = "test_data"

# read the manifest table (one line for each case)
rows = list(csv.DictReader(open(folder + "/MANIFEST.csv")))

all_ids = []
code_mixed = []
planted = []
for row in rows:
    all_ids.append(row["id"])
    if row["language"] == "code-mixed":
        code_mixed.append(row["id"])
    if row["planted_error"] != "none":
        planted.append(row["id"] + ":" + row["planted_error"])

# find which transcript and summary files exist
transcripts = []
summaries = []
for name in os.listdir(folder):
    if name.endswith("_transcript.txt"):
        transcripts.append(name[:3])
    if name.endswith("_expected_summary.txt"):
        summaries.append(name[:3])

missing_transcripts = []
missing_summaries = []
for case_id in all_ids:
    if case_id not in transcripts:
        missing_transcripts.append(case_id)
    if case_id not in summaries:
        missing_summaries.append(case_id)

print("transcripts:", len(transcripts), "/ 20    expected summaries:", len(summaries), "/ 20")
print("code-mixed (planned):", len(code_mixed), "/ 5    planted errors (planned):", len(planted), "/ 10")
print("missing transcript:", missing_transcripts)
print("missing summary:", missing_summaries)
print("planted:", ", ".join(planted))
