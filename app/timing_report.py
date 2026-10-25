# S10: prints the result of the timing sessions.
#   python app/timing_report.py
# It reads results/timing.csv and says PASS or FAIL, or NOT ENOUGH DATA when the sessions
# are not finished (3 people, 20 card timings, and some transcript and approval timings).

import sys

sys.path.insert(0, "app")
from timing import approval_limit, card_limit, faster_limit, make_report, read_times

report = make_report(read_times())


def show(number):
    # a number with one decimal, or "none yet"
    if number is None:
        return "none yet"
    return str(round(number, 1))


print("people:", len(report["people"]), report["people"])
print("card timings:", report["card_count"], " answers not correct (not counted):", report["wrong"])
print("median recall card ....", show(report["card_median"]), "s   (need under", card_limit, "s)")
print("median transcript .....", show(report["transcript_median"]), "s")
print("card is faster by .....", show(report["times_faster"]), "times   (need at least", faster_limit, ")")
print("median approval .......", show(report["approval_median"]), "s   (need under", approval_limit, "s)")
for problem in report["problems"]:
    print("  missing:", problem)
print("S10:", report["verdict"])
