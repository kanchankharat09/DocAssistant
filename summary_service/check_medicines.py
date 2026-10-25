# S6: flag wrong or doubtful medicine names and doses in the AI summaries.
#
# A medicine is flagged when
#   - its name is not in summary_service/formulary.csv (a misspelt name, for example), or
#   - its dose is not one of the usual doses written for that medicine in the formulary.
# The checker does not change anything, it only says what the doctor must look at.
#
# Check one run:     python summary_service/check_medicines.py run2
# Test the checker:  python summary_service/check_medicines.py selftest
#   (selftest uses the doctor-said values, wrong ones included, so it needs no Groq key)
#
# The pass bar: all 10 planted errors flagged, and at most 2 of the 10 clean cases flagged.

import csv
import difflib
import json
import os
import sys

from score_t1 import clean_dose, read_case_medicines, read_manifest

test_data_folder = "test_data"
formulary_file = "summary_service/formulary.csv"


def read_formulary():
    # returns {"paracetamol": ["500mg", "650mg", ...], "ors solution": [""], ...}
    formulary = {}
    for row in csv.DictReader(open(formulary_file, encoding="utf-8")):
        doses = []
        for dose in row["usual_doses"].split("|"):
            doses.append(clean_dose(dose))
        formulary[row["name"].lower()] = doses
    return formulary


def check_medicine(name, dose, formulary):
    # returns a sentence saying what is doubtful, or "" if the medicine looks fine
    name = name.lower().strip()
    dose = clean_dose(dose)
    if name not in formulary:
        close = difflib.get_close_matches(name, list(formulary.keys()), n=1, cutoff=0.7)
        if len(close) > 0:
            return "name '" + name + "' is not known, did you mean '" + close[0] + "'?"
        return "name '" + name + "' is not known"
    if dose not in formulary[name]:
        usual = " or ".join(formulary[name])
        return name + " " + (dose or "(no dose)") + " is not a usual dose, usual: " + usual
    return ""


def check_case(ai_medicines, formulary):
    flags = []
    for medicine in ai_medicines:
        flag = check_medicine(medicine["name"], medicine["dose"], formulary)
        if flag != "":
            flags.append(flag)
    return flags


def check_folder(folder):
    formulary = read_formulary()
    manifest = read_manifest()
    planted_flagged = 0
    planted_total = 0
    clean_flagged = 0
    clean_total = 0
    for case_id in sorted(manifest.keys()):
        json_file = folder + "/" + case_id + ".json"
        if not os.path.exists(json_file):
            print(case_id, "no AI summary in", folder)
            continue
        ai = json.loads(open(json_file, encoding="utf-8").read())["summary"]["medicines"]
        flags = check_case(ai, formulary)
        planted = manifest[case_id]["planted_error"] != "none"
        if planted:
            planted_total = planted_total + 1
            if len(flags) > 0:
                planted_flagged = planted_flagged + 1
        else:
            clean_total = clean_total + 1
            if len(flags) > 0:
                clean_flagged = clean_flagged + 1
        label = "planted " + manifest[case_id]["planted_error"] if planted else "clean"
        if len(flags) > 0:
            print(case_id, "FLAGGED (" + label + ")", flags)
        else:
            print(case_id, "no flag (" + label + ")")
    print("planted errors flagged:", planted_flagged, "of", planted_total, "(need all)")
    print("clean cases wrongly flagged:", clean_flagged, "of", clean_total, "(at most 2)")
    if planted_total == 10 and clean_total == 10:
        if planted_flagged == 10 and clean_flagged <= 2:
            print("S6: PASS")
        else:
            print("S6: FAIL")
    else:
        print("only", planted_total, "planted and", clean_total, "clean cases found, the pass bar needs 10 and 10")
    return planted_flagged, clean_flagged


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        folder = "results/selftest/s6"
        os.makedirs(folder, exist_ok=True)
        for case_id in read_manifest().keys():
            medicines = []
            for medicine_name, dose in read_case_medicines(case_id):
                medicines.append({"name": medicine_name, "dose": dose})
            open(folder + "/" + case_id + ".json", "w").write(json.dumps({"summary": {"medicines": medicines}}))
        check_folder(folder)
    else:
        run_name = "run2"
        if len(sys.argv) > 1:
            run_name = sys.argv[1]
        check_folder("results/summaries/" + run_name)


if __name__ == "__main__":
    main()
