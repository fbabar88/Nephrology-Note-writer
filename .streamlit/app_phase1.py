import streamlit as st
import json
import datetime

# Initialize or load patient data in session state
if "patients" not in st.session_state:
    # Simulated patient records; later you can replace this with a persistent database
    st.session_state.patients = [
        {
            "id": "AB",
            "note_type": "Consult",
            "reason": "AKI secondary to hypovolemia",
            "note": "Initial consultation note details for AB..."
        },
        {
            "id": "CD",
            "note_type": "Progress",
            "reason": "Follow-up on AKI and fluid management",
            "note": "Progress note details for CD..."
        }
    ]

if "current_patient" not in st.session_state:
    st.session_state.current_patient = None

st.title("Active Patient Dashboard")

st.write("### Active Patients")
# Prepare a list of patient display strings
patient_options = [
    f"{patient['id']} - {patient['note_type']} - {patient['reason']}" 
    for patient in st.session_state.patients
]
selected_patient = st.selectbox("Select a patient", patient_options)

# When a patient is selected, load their details
if selected_patient:
    # Extract the patient ID from the selected string
    selected_id = selected_patient.split(" - ")[0]
    patient_record = next((p for p in st.session_state.patients if p["id"] == selected_id), None)
    if patient_record:
        st.session_state.current_patient = patient_record
        st.write("### Patient Details")
        st.write(f"**Patient ID:** {patient_record['id']}")
        st.write(f"**Note Type:** {patient_record['note_type']}")
        st.write(f"**Reason for Consult:** {patient_record['reason']}")

        # Display the patient's note in a text area for editing
        updated_note = st.text_area("Patient Note:", value=patient_record["note"], height=300)

        # Button to update and save the note changes
        if st.button("Update Note"):
            patient_record["note"] = updated_note
            # Optionally, add a timestamp or versioning info here
            patient_record["last_updated"] = str(datetime.datetime.now())
            st.success("Patient note updated successfully!")
            st.write("#### Updated Patient Record:")
            st.json(patient_record)
