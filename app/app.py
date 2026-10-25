# S9 screen: search a patient by name and see the recall card of the last approved visit.
#
# Run it from the main folder:
#   pip install streamlit
#   python3 db/seed.py                 (once, to make clinic.db)
#   streamlit run app/app.py

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))
from recall import find_patients, get_recall_card

st.title("Patient History Assistant")
st.caption("Fictional patients only. Nothing here is real patient data.")

if not os.path.exists("clinic.db"):
    st.error("clinic.db was not found. Run  python3 db/seed.py  from the main folder first.")
    st.stop()

search_text = st.text_input("Search a patient by name")

if search_text.strip() != "":
    patients = find_patients(search_text)
    if len(patients) == 0:
        st.warning("No patient found.")
    else:
        # show the names as a list; if only one patient is found, he or she is chosen already
        labels = []
        for patient in patients:
            labels.append(patient["name"] + ", " + str(patient["age"]) + patient["sex"])
        choice = st.selectbox("Patients found", labels)
        patient = patients[labels.index(choice)]

        card = get_recall_card(patient["patient_id"])
        if card is None:
            st.info("This patient has no approved visit yet.")
        else:
            st.subheader("Recall card: " + card["name"])
            st.write("**Last visit:** " + card["visit_date"])
            st.write("**Main complaint:** " + card["main_complaint"])
            st.write("**Medicines:**")
            for line in card["medicines"].split("\n"):
                st.write("- " + line)
            st.write("**Follow-up advice:** " + card["follow_up_advice"])
