# S10: save the timings of the role-play sessions and work out the result.
#
# One timing is one line in results/timing.csv:
#   time, person, task, patient, seconds, correct
#     person   a label like R1, R2, R3 (use labels, not full names)
#     task     card (find the last visit on the recall card)
#              transcript (find it by reading the full transcript)
#              approval (review the summary and press Approve)
#     patient  the patient of the task
#     seconds  how long it took
#     correct  yes or no: was the answer right?
# The screen (app/pages/2_Timing.py) saves the timings, app/timing_report.py prints the result.

import csv
import os
from datetime import datetime

timing_file = "results/timing.csv"
header = ["time", "person", "task", "patient", "seconds", "correct"]

# the numbers of the plan
card_limit = 15            # median of the card must be under 15 seconds
faster_limit = 2           # the card must be at least 2 times faster than the transcript
approval_limit = 30        # median of the approval must be under 30 seconds
people_needed = 3          # 3 role-players
cards_needed = 20          # 20 cards


def record_time(person, task, patient, seconds, correct):
    # adds one timing at the end of the file (and writes the header line the first time)
    is_new = not os.path.exists(timing_file)
    os.makedirs(os.path.dirname(timing_file), exist_ok=True)
    out_file = open(timing_file, "a", newline="", encoding="utf-8")
    writer = csv.writer(out_file)
    if is_new:
        writer.writerow(header)
    writer.writerow([datetime.now().isoformat(timespec="seconds"), person, task, patient, round(seconds, 1), correct])
    out_file.close()


def read_times():
    # returns all timings as a list of dictionaries (empty list if there is no file yet)
    if not os.path.exists(timing_file):
        return []
    rows = []
    for row in csv.DictReader(open(timing_file, newline="", encoding="utf-8")):
        row["seconds"] = float(row["seconds"])
        rows.append(row)
    return rows


def median(numbers):
    # the middle number of a list; for an even count, the mean of the two middle numbers
    ordered = sorted(numbers)
    middle = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def make_report(rows):
    # works out the numbers of the plan. Only correct answers count in the medians.
    report = {"people": [], "card_count": 0, "wrong": 0,
              "card_median": None, "transcript_median": None, "approval_median": None,
              "times_faster": None, "problems": [], "verdict": ""}

    card = []
    transcript = []
    approval = []
    for row in rows:
        if row["person"] not in report["people"]:
            report["people"].append(row["person"])
        if row["task"] == "card":
            report["card_count"] = report["card_count"] + 1
        if row["correct"] != "yes":
            report["wrong"] = report["wrong"] + 1
            continue
        if row["task"] == "card":
            card.append(row["seconds"])
        elif row["task"] == "transcript":
            transcript.append(row["seconds"])
        elif row["task"] == "approval":
            approval.append(row["seconds"])

    if len(card) > 0:
        report["card_median"] = median(card)
    if len(transcript) > 0:
        report["transcript_median"] = median(transcript)
    if len(approval) > 0:
        report["approval_median"] = median(approval)
    if report["card_median"] is not None and report["transcript_median"] is not None:
        report["times_faster"] = report["transcript_median"] / report["card_median"]

    # not enough data: the verdict must not be PASS or FAIL
    if len(report["people"]) < people_needed:
        report["problems"].append("only " + str(len(report["people"])) + " people, need " + str(people_needed))
    if report["card_count"] < cards_needed:
        report["problems"].append("only " + str(report["card_count"]) + " card timings, need " + str(cards_needed))
    if report["transcript_median"] is None:
        report["problems"].append("no correct transcript timing yet")
    if report["approval_median"] is None:
        report["problems"].append("no correct approval timing yet")
    if len(report["problems"]) > 0:
        report["verdict"] = "NOT ENOUGH DATA"
        return report

    if (report["card_median"] < card_limit and report["times_faster"] >= faster_limit
            and report["approval_median"] < approval_limit):
        report["verdict"] = "PASS"
    else:
        report["verdict"] = "FAIL"
    return report
