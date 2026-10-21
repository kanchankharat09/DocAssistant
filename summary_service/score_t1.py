# S4: score T1 = how many AI summaries keep every medicine name and dose of the expected summary.
#
# Score one run:     python summary_service/score_t1.py run1
# Test the scorer:   python summary_service/score_t1.py selftest
#   (selftest makes a perfect copy from the expected summaries and scores it,
#    then removes one dose and scores again, so the second must be one lower)
#
# This version checks medicine name and dose only. Symptoms, duration, history
# and frequency still have to be read by hand for now.

import csv
import json
import os
import sys
from datetime import datetime

test_data_folder = "test_data"


def clean_dose(text):
    # makes small letters, removes spaces, and writes units the same way (75 micrograms and 75mcg become the same)
    text = text.lower().replace(" ", "")
    text = text.replace("micrograms", "mcg").replace("microgram", "mcg")
    text = text.replace("milligrams", "mg").replace("milligram", "mg")
    return text


def read_expected_medicines(file_name):
    # reads the lines like "- Paracetamol 500mg — three times a day after food — 3 days"
    # returns a list of (name, dose) pairs in small letters, like ("paracetamol", "500mg")
    medicines = []
    in_medicines = False
    for line in open(file_name, encoding="utf-8").read().split("\n"):
        if line.startswith("Medicines prescribed:"):
            in_medicines = True
        elif in_medicines and line.startswith("- "):
            first_part = line[2:].split(" — ")[0]          # example: Paracetamol 500mg
            name_words = []
            dose_words = []
            for word in first_part.split(" "):
                has_digit = False
                for letter in word:
                    if letter.isdigit():
                        has_digit = True
                if has_digit or len(dose_words) > 0:
                    dose_words.append(word)
                else:
                    name_words.append(word)
            medicines.append((" ".join(name_words).lower(), clean_dose("".join(dose_words))))
        else:
            in_medicines = False
    return medicines


def case_passes(expected_medicines, ai_medicines):
    # every expected medicine must be found in the AI list with the same name and dose
    for expected_name, expected_dose in expected_medicines:
        found = False
        for ai in ai_medicines:
            ai_name = ai["name"].lower().strip()
            ai_dose = clean_dose(ai["dose"])
            if expected_name.split(" ")[0] in ai_name and expected_dose == ai_dose:
                found = True
        if not found:
            return False
    return True


def score_folder(folder):
    passed = 0
    total = 0
    for name in sorted(os.listdir(test_data_folder)):
        if not name.endswith("_expected_summary.txt"):
            continue
        case_id = name[:3]
        json_file = folder + "/" + case_id + ".json"
        if not os.path.exists(json_file):
            print(case_id, "no AI summary in", folder)
            continue
        total = total + 1
        expected = read_expected_medicines(test_data_folder + "/" + name)
        ai = json.loads(open(json_file, encoding="utf-8").read())["summary"]["medicines"]
        if case_passes(expected, ai):
            passed = passed + 1
            print(case_id, "pass")
        else:
            print(case_id, "FAIL   expected:", expected)
            print("        AI gave:", [(m["name"], m["dose"]) for m in ai])
    return passed, total


if len(sys.argv) > 1 and sys.argv[1] == "selftest":
    # make a perfect folder from the expected summaries
    perfect_folder = "results/selftest/perfect"
    broken_folder = "results/selftest/broken"
    os.makedirs(perfect_folder, exist_ok=True)
    os.makedirs(broken_folder, exist_ok=True)
    first_case = True
    for name in sorted(os.listdir(test_data_folder)):
        if not name.endswith("_expected_summary.txt"):
            continue
        medicines = []
        for medicine_name, dose in read_expected_medicines(test_data_folder + "/" + name):
            medicines.append({"name": medicine_name, "dose": dose})
        perfect = {"summary": {"medicines": medicines}}
        open(perfect_folder + "/" + name[:3] + ".json", "w").write(json.dumps(perfect))
        if first_case and len(medicines) > 0:
            medicines = [{"name": medicines[0]["name"], "dose": ""}] + medicines[1:]   # one dose removed
            first_case = False
        broken = {"summary": {"medicines": medicines}}
        open(broken_folder + "/" + name[:3] + ".json", "w").write(json.dumps(broken))
    print("--- perfect copy ---")
    p1, t1 = score_folder(perfect_folder)
    print("--- copy with one dose removed ---")
    p2, t2 = score_folder(broken_folder)
    print("perfect:", p1, "of", t1, "  broken:", p2, "of", t2)
else:
    run_name = "run1"
    if len(sys.argv) > 1:
        run_name = sys.argv[1]
    passed, total = score_folder("results/summaries/" + run_name)
    print("T1 score:", passed, "of", total)

    # write this score in the results sheet (S5). it keeps the model and the prompt of the run.
    model_used = ""
    prompt_used = ""
    first_json = "results/summaries/" + run_name
    for name in sorted(os.listdir(first_json)):
        if name.endswith(".json"):
            info = json.loads(open(first_json + "/" + name, encoding="utf-8").read())
            model_used = info.get("model", "")
            prompt_used = info.get("prompt_file", "")
            break
    sheet = "results/results_sheet.csv"
    is_new = not os.path.exists(sheet)
    sheet_file = open(sheet, "a", newline="", encoding="utf-8")
    writer = csv.writer(sheet_file)
    if is_new:
        writer.writerow(["time", "run", "model", "prompt_file", "passed", "total"])
    writer.writerow([datetime.now().isoformat(timespec="seconds"), run_name, model_used, prompt_used, passed, total])
    sheet_file.close()
    print("written in", sheet)

    if total == 20:
        if passed >= 18:
            print("T1: PASS (needs at least 18 of 20)")
        else:
            print("T1: FAIL (needs at least 18 of 20)")
    else:
        print("only", total, "transcripts so far, the pass bar needs all 20")
