import streamlit as st
import openai
import json
import datetime

# Configure the OpenAI SDK for DeepSeek (Beta Endpoint)
openai.api_base = "https://api.deepseek.com/beta"  # Use the beta endpoint
openai.api_key = st.secrets.get("DEEPSEEK_API_KEY", "")  # Add your API key to Streamlit secrets

# Initialize or load patient data in session state
if "patients" not in st.session_state:
    # Simulated patient records; later replace with persistent storage/database
    st.session_state.patients = [
        {
            "id": "AB",
            "note_type": "Consult",  # "Consult" for initial, "Progress" for follow-up
            "reason": "AKI secondary to hypovolemia",
            "consultation_note": "",
            "soap_note": "",
            "last_updated": str(datetime.datetime.now())
        },
        {
            "id": "CD",
            "note_type": "Progress",
            "reason": "Follow-up on AKI and fluid management",
            "consultation_note": "",
            "soap_note": "",
            "last_updated": str(datetime.datetime.now())
        }
    ]

if "current_patient" not in st.session_state:
    st.session_state.current_patient = None

# Sidebar: Active Patient List
st.sidebar.title("Active Patients")
patient_options = [
    f"{p['id']} - {p['note_type']} - {p['reason']}" for p in st.session_state.patients
]
selected_patient = st.sidebar.selectbox("Select a patient", patient_options)

if selected_patient:
    # Extract patient ID from selected string and load the record
    selected_id = selected_patient.split(" - ")[0]
    patient_record = next((p for p in st.session_state.patients if p["id"] == selected_id), None)
    st.session_state.current_patient = patient_record

    st.header(f"Patient {patient_record['id']} - {patient_record['note_type']}")
    st.write(f"**Reason for Consult:** {patient_record['reason']}")
    st.write(f"**Last Updated:** {patient_record.get('last_updated', 'N/A')}")

    # Create tabs for the two note generation modes
    tab1, tab2 = st.tabs(["Consultation Note", "SOAP Note"])

    with tab1:
        st.subheader("Generate Consultation Note")
        # Pre-populate the reason from the patient record
        reason = st.text_input("Reason for Consultation:", patient_record["reason"])
        symptoms = st.text_area("Presenting Symptoms:", "", height=80)
        context_history = st.text_area("Clinical History & Context:", "", height=80)
        labs = st.text_area("Labs:", "", height=80)
        assessment_plan_input = st.text_area(
            "Assessment & Plan:",
            "Enter a combined list of problem headings and corresponding treatment options.\n"
            "For example:\n"
            "AKI: Optimize fluid management, avoid nephrotoxic agents, consider RRT if indicated.\n"
            "Metabolic Acidosis: Monitor acid-base status, administer bicarbonate if pH < 7.2.\n"
            "Cardiogenic Shock: Adjust pressor support and collaborate with cardiology.",
            height=150
        )

        if st.button("Generate Consultation Note"):
            prompt = f"""
Generate a comprehensive Epic consultation note in the style of a board-certified nephrologist using the following inputs:

**Reason for Consultation:**
{reason}

**Presenting Symptoms:**
{symptoms}

**Clinical History & Context:**
{context_history}

**Labs:**
{labs}

**Assessment & Plan (Targeted):**
{assessment_plan_input}

Based on the above, generate a note that includes:
1. **Reason for Consultation:** Restate the consultation reason.
2. **History of Present Illness (HPI):** Provide a concise narrative summarizing the presenting symptoms, clinical history & context, and labs.
3. **Assessment and Plan:** For each problem mentioned in the 'Assessment & Plan' input, elaborate a brief assessment using clinical details from the HPI and then integrate the corresponding targeted treatment options.
Do not add any extra summary sections.
"""
            with st.spinner("Generating Consultation Note..."):
                response = openai.Completion.create(
                    model="deepseek-chat",
                    prompt=prompt,
                    max_tokens=1200,
                    temperature=0.7,
                )
                generated_note = response.choices[0].text.strip()
                # Save the generated consultation note in the patient record
                patient_record["consultation_note"] = generated_note
                patient_record["note_type"] = "Consult"
                patient_record["last_updated"] = str(datetime.datetime.now())
                st.success("Consultation note generated and saved!")
                st.text_area("Consultation Note:", value=generated_note, height=400)

    with tab2:
        st.subheader("Generate SOAP Note")
        case_update = st.text_area("Case Update:", "Enter a comprehensive update on the case", height=150)

        if st.button("Generate SOAP Note"):
            if not patient_record.get("consultation_note"):
                st.error("Please generate a consultation note first.")
            else:
                soap_prompt = f"""
Using the following consultation note and case update, generate a SOAP note for a progress note in the style of a board-certified nephrologist.
In the SOAP note:
- **Subjective:** Provide a concise statement of the patient's current condition using the case update.
- **Assessment and Plan:** Reflect the problem list and treatment options as provided in the consultation note.
- **Objective:** Omit this section.

Consultation Note:
{patient_record.get("consultation_note")}

Case Update:
{case_update}

SOAP Note:
"""
                with st.spinner("Generating SOAP Note..."):
                    response = openai.Completion.create(
                        model="deepseek-chat",
                        prompt=soap_prompt,
                        max_tokens=800,
                        temperature=0.7,
                    )
                    soap_note = response.choices[0].text.strip()
                    # Save the generated SOAP note in the patient record
                    patient_record["soap_note"] = soap_note
                    patient_record["note_type"] = "Progress"
                    patient_record["last_updated"] = str(datetime.datetime.now())
                    st.success("SOAP note generated and saved!")
                    st.text_area("SOAP Note:", value=soap_note, height=400)

    # Button to "Save" patient record (simulate persistence)
    if st.button("Save Patient Record"):
        # In a real-world scenario, save to a database or persistent storage
        st.success("Patient record saved!")
        st.json(patient_record)
