# S4 and S5: score T1 = how many AI summaries keep every required detail of the expected summary.
# The six details of the plan: medicine, dose, frequency, symptom, duration, history.
#
# Score one run:     python summary_service/score_t1.py run1
# Test the scorer:   python summary_service/score_t1.py selftest
#   (selftest makes a perfect copy from the expected summaries and scores it,
#    then removes one dose and scores again, so the second must be one lower)
#
# A case passes only if all six details are right. A failed case says what was missing.
#   medicine   every expected medicine is in the AI list (name)
#   dose       the dose of that medicine is the same
#   frequency  the key words of "how often" (once, twice, three, morning, night, fever ...) are there
#   duration   the days of the illness and of each medicine are there (2 weeks = 14 days)
#   symptom    most of the important words of chief complaint + symptoms are there
#   history    most of the important words of past history are there
#
# In the 10 cases with a planted error the doctor said a wrong value (see wrong_value in
# test_data/MANIFEST.csv). The AI passes by keeping what was said, so those cases are checked
# against wrong_value.
#
# The word rules (frequency, symptom, history) are simple and only a first version. If a case
# fails there, read it by hand before you trust the fail.

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


def read_manifest():
    # reads test_data/MANIFEST.csv: for the cases with a planted error, what was said (wrong_value)
    # and what is right (correct_value)
    manifest = {}
    for row in csv.DictReader(open(test_data_folder + "/MANIFEST.csv", encoding="utf-8")):
        manifest[row["id"]] = row
    return manifest


def read_case_medicines(case_id):
    # what the AI should write for this case. the AI must copy what the doctor said, so in the
    # cases with a planted error the wrong value (not the right one) is the expected answer.
    medicines = read_expected_medicines(test_data_folder + "/" + case_id + "_expected_summary.txt")
    row = read_manifest().get(case_id)
    if row is None or row["wrong_value"] == "":
        return medicines
    wrong = row["wrong_value"].lower()
    correct = row["correct_value"].lower()
    changed = []
    for name, dose in medicines:
        if row["planted_error"] == "dose" and dose == clean_dose(correct):
            dose = clean_dose(wrong)
        if row["planted_error"] == "name" and name == correct:
            name = wrong
        changed.append((name, dose))
    return changed


def read_expected_details(case_id):
    # reads the expected summary of a case into a small dictionary
    file_name = test_data_folder + "/" + case_id + "_expected_summary.txt"
    details = {"chief_complaint": "", "duration": "", "associated_symptoms": "", "past_history": ""}
    names = {"Chief complaint:": "chief_complaint", "Duration:": "duration",
             "Associated symptoms:": "associated_symptoms", "Past history:": "past_history"}
    frequencies = []
    durations = []
    in_medicines = False
    for line in open(file_name, encoding="utf-8").read().split("\n"):
        for start in names:
            if line.startswith(start):
                details[names[start]] = line[len(start):].strip()
        if line.startswith("Medicines prescribed:"):
            in_medicines = True
        elif in_medicines and line.startswith("- "):
            parts = line[2:].split(" — ")
            frequencies.append(parts[1] if len(parts) > 1 else "")
            durations.append(parts[2] if len(parts) > 2 else "")
        else:
            in_medicines = False
    medicines = []
    names_and_doses = read_case_medicines(case_id)
    for i in range(len(names_and_doses)):
        medicines.append({"name": names_and_doses[i][0], "dose": names_and_doses[i][1],
                          "frequency": frequencies[i], "duration": durations[i]})
    details["medicines"] = medicines
    return details


frequency_words = ["once", "twice", "three", "four", "morning", "evening", "night", "bedtime", "fever", "needed", "hours", "every"]


def frequency_key_words(text):
    text = text.lower()
    text = text.replace("thrice", "three").replace("daily", "once").replace("two times", "twice")
    keys = []
    for word in frequency_words:
        if word in text:
            keys.append(word)
    return keys


def days_in(text):
    # "3 days" -> 3, "2 weeks" -> 14, "1 month" -> 30. returns the list of numbers of days
    days = []
    words = text.lower().replace("-", " ").split(" ")
    for i in range(len(words) - 1):
        if words[i].isdigit():
            unit = words[i + 1]
            if unit.startswith("day"):
                days.append(int(words[i]))
            elif unit.startswith("week"):
                days.append(int(words[i]) * 7)
            elif unit.startswith("month"):
                days.append(int(words[i]) * 30)
    return days


skip_words = ["with", "that", "this", "from", "have", "been", "also", "than", "which", "there",
              "since", "after", "before", "none", "other", "illness", "history", "complaint", "mild", "past"]


def important_words(text):
    words = []
    for word in text.lower().replace(",", " ").replace(".", " ").replace("-", " ").split(" "):
        if len(word) >= 4 and word not in skip_words and not word.isdigit():
            words.append(word)
    return words


def words_are_there(expected_text, ai_text):
    # at least 60 percent of the important words of the expected text must be in the AI text
    wanted = important_words(expected_text)
    if len(wanted) == 0:
        return True
    found = 0
    for word in wanted:
        if word[:5] in ai_text.lower():
            found = found + 1
    return found * 10 >= len(wanted) * 6


def what_is_missing(expected, ai):
    # returns the list of details that are missing, [] means the case passes
    missing = []
    ai_medicines = ai.get("medicines", [])
    for medicine in expected["medicines"]:
        found = None
        for ai_medicine in ai_medicines:
            if medicine["name"].split(" ")[0] in ai_medicine["name"].lower().strip():
                found = ai_medicine
        if found is None:
            missing.append("medicine " + medicine["name"])
            continue
        if clean_dose(found["dose"]) != medicine["dose"]:
            missing.append("dose of " + medicine["name"])
        for key in frequency_key_words(medicine["frequency"]):
            if key not in frequency_key_words(found["frequency"]):
                missing.append("frequency of " + medicine["name"])
                break
        for number in days_in(medicine["duration"]):
            if number not in days_in(found["duration"]):
                missing.append("duration of " + medicine["name"])
                break
    for number in days_in(expected["duration"]):
        if number not in days_in(ai.get("duration", "")):
            missing.append("duration of the illness")
            break
    if not words_are_there(expected["chief_complaint"] + " " + expected["associated_symptoms"],
                           ai.get("chief_complaint", "") + " " + ai.get("associated_symptoms", "")):
        missing.append("symptom")
    if not words_are_there(expected["past_history"], ai.get("past_history", "")):
        missing.append("history")
    return missing


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
        expected = read_expected_details(case_id)
        ai = json.loads(open(json_file, encoding="utf-8").read())["summary"]
        missing = what_is_missing(expected, ai)
        if len(missing) == 0:
            passed = passed + 1
            print(case_id, "pass")
        else:
            print(case_id, "FAIL   missing:", missing)
    return passed, total


def main():
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
            details = read_expected_details(name[:3])
            medicines = details["medicines"]
            perfect = {"summary": details}
            open(perfect_folder + "/" + name[:3] + ".json", "w").write(json.dumps(perfect))
            if first_case and len(medicines) > 0:
                medicines = [dict(medicines[0], dose="")] + medicines[1:]   # one dose removed
                first_case = False
            broken = {"summary": dict(details, medicines=medicines)}
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
        # what the prompt changed compared with prompt_v1 (the lines that v1 does not have)
        prompt_change = ""
        if prompt_used != "" and os.path.exists(prompt_used):
            v1_lines = open("summary_service/prompt_v1.txt", encoding="utf-8").read().split("\n")
            changed_lines = []
            for line in open(prompt_used, encoding="utf-8").read().split("\n"):
                if line.strip() != "" and line not in v1_lines:
                    changed_lines.append(line.strip())
            prompt_change = " ".join(changed_lines)
        if prompt_change == "":
            prompt_change = "same as prompt_v1"
        sheet = "results/results_sheet.csv"
        header = ["time", "run", "model", "prompt_file", "passed", "total", "prompt_change"]
        old_rows = []
        if os.path.exists(sheet):
            old_rows = list(csv.reader(open(sheet, newline="", encoding="utf-8")))
        sheet_file = open(sheet, "w", newline="", encoding="utf-8")
        writer = csv.writer(sheet_file)
        writer.writerow(header)
        for row in old_rows[1:]:
            while len(row) < len(header):
                row.append("")
            writer.writerow(row)
        writer.writerow([datetime.now().isoformat(timespec="seconds"), run_name, model_used, prompt_used, passed, total, prompt_change])
        sheet_file.close()
        print("written in", sheet)

        if total == 20:
            if passed >= 18:
                print("T1: PASS (needs at least 18 of 20)")
            else:
                print("T1: FAIL (needs at least 18 of 20)")
        else:
            print("only", total, "transcripts so far, the pass bar needs all 20")


if __name__ == "__main__":
    main()
