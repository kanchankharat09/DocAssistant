# S7 and S8 screen: shows the AI summary and its flags. Approve is blocked until every flag
# is fixed or dismissed. Approve saves the visit (S8) and every action goes in the audit log.
#
# Run:  streamlit run app/app.py     and open "Review" in the left menu.

import os
import sys

import streamlit as st

sys.path.insert(0, "app")
from review import fix_medicine, load_summary, open_flags
from save import approve_and_save, leave_unapproved

st.title("Review the summary")
st.caption("Fictional patients only.")

# the AI summaries of the run we want to review
run_folder = "results/summaries/run2"
if not os.path.exists(run_folder):
    st.error("Folder " + run_folder + " was not found. Run summarize.py first.")
    st.stop()

case_ids = []
for name in sorted(os.listdir(run_folder)):
    if name.endswith(".json"):
        case_ids.append(name[:-5])
case_id = st.selectbox("Case", case_ids)

# st.session_state keeps the changes of the doctor while the page is used
if st.session_state.get("case_id") != case_id:
    st.session_state["case_id"] = case_id
    st.session_state["summary"] = load_summary(run_folder, case_id)
    st.session_state["dismissed"] = []
summary = st.session_state["summary"]
dismissed = st.session_state["dismissed"]

# the summary
st.subheader("Summary")
st.write("**Main complaint:** " + summary.get("chief_complaint", ""))
st.write("**Duration:** " + summary.get("duration", ""))
st.write("**Symptoms:** " + summary.get("associated_symptoms", ""))
st.write("**Past history:** " + summary.get("past_history", ""))
st.write("**Allergies:** " + summary.get("allergies", ""))
st.write("**Doctor instructions:** " + summary.get("doctor_instructions", ""))
st.write("**Medicines:**")
for medicine in summary.get("medicines", []):
    st.write("- " + medicine["name"] + " " + medicine["dose"] + " | " + medicine.get("frequency", "") + " | " + medicine.get("duration", ""))

# the flags that are not handled yet
st.subheader("Flags")
waiting = open_flags(summary, dismissed)
if len(waiting) == 0:
    st.success("No flag is waiting.")
for flag in waiting:
    medicine = summary["medicines"][flag["medicine_number"]]
    st.warning(flag["message"])
    new_name = st.text_input("Medicine name", value=medicine["name"], key="name" + flag["key"])
    new_dose = st.text_input("Dose", value=medicine["dose"], key="dose" + flag["key"])
    if st.button("Fix", key="fix" + flag["key"]):
        st.session_state["summary"] = fix_medicine(summary, flag["medicine_number"], new_name, new_dose)
        st.rerun()
    if st.button("Dismiss (it is fine)", key="dismiss" + flag["key"]):
        dismissed.append(flag["key"])
        st.rerun()

# Approve (S8: saves the visit) or leave the summary unapproved (nothing is saved)
st.subheader("Approve")
if not os.path.exists("clinic.db"):
    st.error("clinic.db was not found. Run  python3 db/seed.py  first.")
    st.stop()
if st.button("Approve and save"):
    allowed, text = approve_and_save(case_id, summary, dismissed)
    if allowed:
        st.success(text)
    else:
        st.error(text)
if st.button("Leave unapproved"):
    leave_unapproved(case_id)
    st.info("Left unapproved. Nothing was saved.")
