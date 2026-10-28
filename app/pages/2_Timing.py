# S10 screen: a stopwatch for the role-play sessions.
# You choose the person, the task and the patient, press Start, press Stop when the person
# has told all the details, say if the answer was correct, and save the timing.
# The timings go in results/timing.csv.

import sys
import time

import streamlit as st

sys.path.insert(0, "app")
from recall import find_patients, get_recall_card
from timing import make_report, read_times, record_time

st.title("Timing session")
st.caption("Use labels like R1, R2, R3 for the role-players, not full names.")

person = st.text_input("Role-player label", value="R1")
task = st.selectbox("Task", ["card", "transcript", "approval"])
names = []
for patient in find_patients(""):          # an empty search text gives all the patients
    names.append(patient["name"])
patient_name = st.selectbox("Patient", names)

# the right answer, for you (the observer) to compare with what the role-player says.
# It is closed at first. Do not open it while the role-player can see this page.
if task in ["card", "transcript"]:
    with st.expander("Show the right answer (observer only)"):
        found = find_patients(patient_name)
        card = None
        if len(found) > 0:
            card = get_recall_card(found[0]["patient_id"])
        if card is None:
            st.write("No card found.")
        else:
            st.write("**Last visit:** " + card["visit_date"])
            st.write("**Main complaint:** " + card["main_complaint"])
            st.write("**Medicines:**")
            for line in card["medicines"].split("\n"):
                st.write("- " + line)
            st.write("**Follow-up advice:** " + card["follow_up_advice"])

# st.session_state keeps the start time between the clicks
if st.button("Start"):
    st.session_state["start"] = time.time()
    st.session_state["seconds"] = None
if st.button("Stop"):
    if st.session_state.get("start") is None:
        st.warning("Press Start first.")
    else:
        st.session_state["seconds"] = time.time() - st.session_state["start"]
        st.session_state["start"] = None

seconds = st.session_state.get("seconds")
if seconds is not None:
    st.write("Time: **" + str(round(seconds, 1)) + " seconds**")
    correct = st.radio("Was the answer correct?", ["yes", "no"])
    if st.button("Save this timing"):
        record_time(person, task, patient_name, seconds, correct)
        st.session_state["seconds"] = None
        st.success("Saved.")

st.subheader("So far")
rows = read_times()
st.write("Timings saved:", len(rows))
report = make_report(rows)
st.write("People:", len(report["people"]), "| Verdict now:", report["verdict"])
