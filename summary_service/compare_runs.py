# S3 second test: do two runs give the same medicines and doses?
# First make two runs:
#   $env:RUN_NAME="run1"; python summary_service/summarize.py
#   $env:RUN_NAME="run2"; python summary_service/summarize.py
# Then:  python summary_service/compare_runs.py

import json
import os

folder1 = "results/summaries/run1"
folder2 = "results/summaries/run2"


def medicine_list(file_name):
    # returns the medicines as a sorted list of (name, dose) pairs, small letters
    data = json.loads(open(file_name, encoding="utf-8").read())
    pairs = []
    for medicine in data["summary"]["medicines"]:
        pairs.append((medicine["name"].lower().strip(), medicine["dose"].lower().strip()))
    pairs.sort()
    return pairs


files = sorted(os.listdir(folder1))
same_count = 0
total_count = 0

for file_name in files:
    if not file_name.endswith(".json"):
        continue
    if not os.path.exists(folder2 + "/" + file_name):
        print(file_name[:3], "missing in run2")
        continue

    total_count = total_count + 1
    first = medicine_list(folder1 + "/" + file_name)
    second = medicine_list(folder2 + "/" + file_name)

    if first == second:
        same_count = same_count + 1
        print(file_name[:3], "same")
    else:
        print(file_name[:3], "DIFFERENT")
        print("   run1:", first)
        print("   run2:", second)

print("same medicines and doses on", same_count, "of", total_count)
if total_count == 20:
    if same_count >= 18:
        print("S3 repeat test: PASS (needs at least 18 of 20)")
    else:
        print("S3 repeat test: FAIL (needs at least 18 of 20)")
else:
    print("only", total_count, "transcripts so far, the pass bar needs all 20")
