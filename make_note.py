# S12: writes the results note (one page) from the numbers that were measured.
#   python make_note.py
# It reads
#   results/final_run.txt   the final run of T1 to T5 (S11, made by run_tests.py)
#   results/timing.csv      the role-play timings (S10)
# and writes results_note.txt. It cannot invent a number: a test with no result says
# NOT MEASURED, and then it makes no call.
# You write section 4 in note_found.txt and section 6 in note_next.txt (one line each, in your own words).
# Until then the note shows the lines marked [WRITE ...].
#
# The call follows the hypothesis of step.md (Hitesh must agree with this reading):
#   STOP  a "we are wrong" rule is true: T1 below 16 of 20, a wrong dose saved without a flag
#         (T2 fails), or the card is less than 2x faster than the transcript
#   GO    all five tests Pass, the card median is under 15 s and the card is at least 2x faster
#   FIX   everything else (this includes T1 of 16 or 17, which the plan calls inconclusive)

import os
import sys

sys.path.insert(0, "app")
from timing import make_report, read_times

final_run_file = "results/final_run.txt"
note_file = "results_note.txt"
page_limit = 45          # about one page


def read_final_run(file_name):
    # reads the table of run_tests.py. Returns the header lines and a dictionary:
    #   "T1" -> {"name": ..., "target": ..., "result": ..., "verdict": "Pass" / "Fail" / "NOT MEASURED" / "NOT RUN"}
    header = []
    tests = {}
    for line in open(file_name, encoding="utf-8").read().split("\n"):
        if line.strip() == "":
            continue
        if len(line) > 2 and line[0] == "T" and line[1].isdigit() and "):  " in line:
            key = line[:2]
            name = line[2:].split("(need")[0].strip()
            target = line.split("(need ")[1].split("):  ")[0]
            result = line.split("):  ", 1)[1].strip()
            if "NOT MEASURED" in result:
                verdict = "NOT MEASURED"
            elif result.startswith("NOT RUN"):
                verdict = "NOT RUN"
            elif "Pass" in result.split():
                verdict = "Pass"
            elif "Fail" in result.split():
                verdict = "Fail"
            else:
                verdict = "NOT RUN"
            tests[key] = {"name": name, "target": target, "result": result, "verdict": verdict}
        else:
            header.append(line)
    return header, tests


def read_text_lines(file_name, placeholder):
    # the lines of a small text file written by you (note_found.txt or note_next.txt).
    # If the file is not there or is empty, the placeholder line is used.
    if os.path.exists(file_name):
        lines = []
        for line in open(file_name, encoding="utf-8").read().split("\n"):
            if line.strip() != "":
                lines.append("   " + line.strip())
        if len(lines) > 0:
            return lines
    return ["   " + placeholder]


def first_number(text):
    # the first whole number in a text, or None
    for word in text.replace(",", " ").split(" "):
        if word.isdigit():
            return int(word)
    return None


def make_call(tests, speed):
    # returns (call, reason)
    missing = []
    for key in ["T1", "T2", "T3", "T4", "T5"]:
        if key not in tests or tests[key]["verdict"] in ["NOT MEASURED", "NOT RUN"]:
            missing.append(key)
    if speed["times_faster"] is None:
        missing.append("card speed (S10)")

    # the "we are wrong" rules can be checked even when something else is missing
    t1_score = None
    if "T1" in tests:
        t1_score = first_number(tests["T1"]["result"])
    if t1_score is not None and t1_score < 16:
        return "STOP", "T1 is " + str(t1_score) + " of 20, below 16 (a 'we are wrong' rule of the plan)"
    if "T2" in tests and tests["T2"]["verdict"] == "Fail":
        return "STOP", "T2 failed: a planted error was not flagged or Approve was not blocked on a flag"
    if speed["times_faster"] is not None and speed["times_faster"] < 2:
        return "STOP", "the card is only " + str(round(speed["times_faster"], 1)) + " times faster than the transcript (need 2)"

    if len(missing) > 0:
        return "NO CALL YET", "not measured: " + ", ".join(missing)

    all_pass = True
    for key in ["T1", "T2", "T3", "T4", "T5"]:
        if tests[key]["verdict"] != "Pass":
            all_pass = False
    if all_pass and speed["card_median"] < 15:
        return "GO", "all five tests pass and the card is " + str(round(speed["times_faster"], 1)) + " times faster"
    if t1_score in [16, 17]:
        return "FIX", "T1 is " + str(t1_score) + " of 20: inconclusive, fix and run once more (plan rule)"
    failed = []
    for key in ["T1", "T2", "T3", "T4", "T5"]:
        if tests[key]["verdict"] != "Pass":
            failed.append(key)
    if speed["card_median"] >= 15:
        failed.append("card median is not under 15 s")
    return "FIX", "not all targets met: " + ", ".join(failed)


def build_note(header, tests, speed, call, reason):
    lines = []
    lines.append("RESULTS NOTE: Patient History Assistant (MVP on mock data)")
    lines.append("")
    for line in header:
        lines.append(line)
    lines.append("")
    lines.append("1. Tests against their targets")
    for key in ["T1", "T2", "T3", "T4", "T5"]:
        if key in tests:
            lines.append("   " + key + " " + tests[key]["name"] + " | need " + tests[key]["target"] + " | " + tests[key]["result"].split("   (cases")[0])
        else:
            lines.append("   " + key + " | NOT RUN")
    lines.append("")
    lines.append("2. Speed (role-play sessions, S10)")
    if len(speed["people"]) == 0:
        lines.append("   NOT MEASURED (no timing sessions yet)")
    else:
        def show(number):
            if number is None:
                return "not measured"
            return str(round(number, 1))
        lines.append("   People: " + str(len(speed["people"])) + " (need 3), card timings: " + str(speed["card_count"])
                     + " (need 20), answers not correct: " + str(speed["wrong"]))
        lines.append("   Card median " + show(speed["card_median"]) + " s (need under 15), transcript median "
                     + show(speed["transcript_median"]) + " s")
        lines.append("   Card is " + show(speed["times_faster"]) + " times faster (need at least 2), approval median "
                     + show(speed["approval_median"]) + " s (need under 30)")
    lines.append("")
    lines.append("3. Call: " + call)
    lines.append("   Why: " + reason)
    lines.append("   (Suggested by the rules of step.md. The final call is made with Hitesh.)")
    lines.append("")
    lines.append("4. What we found")
    lines = lines + read_text_lines("note_found.txt", "[WRITE 3 to 5 short lines: what worked, what failed, what surprised you]")
    lines.append("")
    lines.append("5. Limits")
    lines.append("   - 20 mock transcripts and 3 role-players, no real patients. The numbers are a first sign, not a proof.")
    lines.append("   - The prompt was tuned on the same 20 transcripts, so the score may be lower on new ones.")
    lines.append("   - The medicine list is a demo list from public drug labels, not checked by a doctor or pharmacist.")
    lines.append("   - The T1 rules for frequency, symptom and history are simple word rules.")
    lines.append("")
    lines.append("6. Next step")
    lines = lines + read_text_lines("note_next.txt", "[WRITE 2 or 3 lines: what we do next if GO or FIX]")
    return lines


def main():
    if not os.path.exists(final_run_file):
        print(final_run_file, "was not found. Run  python run_tests.py  first (S11).")
        return
    header, tests = read_final_run(final_run_file)
    speed = make_report(read_times())
    call, reason = make_call(tests, speed)
    lines = build_note(header, tests, speed, call, reason)
    open(note_file, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("")
    print("saved in", note_file, "(" + str(len(lines)) + " lines)")
    if len(lines) > page_limit:
        print("WARNING: longer than one page (about", page_limit, "lines). Make it shorter.")


if __name__ == "__main__":
    main()
