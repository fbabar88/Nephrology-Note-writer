import streamlit as st
import boto3
import json
import datetime
import tempfile
import re
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer

# Helper function to remove leading asterisks from each line
def remove_leading_asterisks(text):
    cleaned_lines = [re.sub(r"^\s*\*\s*", "", line) for line in text.splitlines()]
    return "\n".join(cleaned_lines)

# Initialize Hugging Face model (using GPT-2 for example)
@st.cache_resource
def load_huggingface_model():
    model_name = "gpt2"  # You can choose any other model from Hugging Face hub
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    generator = pipeline("text-generation", model=model, tokenizer=tokenizer)
    return generator

generator = load_huggingface_model()

# S3 integration functions
def get_s3_client():
    s3 = boto3.client(
        's3',
        aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
        region_name=st.secrets["AWS_DEFAULT_REGION"]
    )
    return s3

def upload_patient_record_to_s3(record):
    s3 = get_s3_client()
    bucket = st.secrets["BUCKET_NAME"]
    timestamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    file_key = f"patients/{record['id']}_{timestamp}.json"
    record_json = json.dumps(record)
    s3.put_object(Body=record_json, Bucket=bucket, Key=file_key)
    st.success(f"Patient record saved to S3 with key: {file_key}")

def load_latest_patient_record_from_s3(patient_id):
    s3 = get_s3_client()
    bucket = st.secrets["BUCKET_NAME"]
    prefix = f"patients/{patient_id}_"
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    
    if 'Contents' not in response:
        st.warning("No records found for this patient in S3.")
        return None

    objects = sorted(response['Contents'], key=lambda obj: obj['LastModified'], reverse=True)
    latest_key = objects[0]['Key']
    obj = s3.get_object(Bucket=bucket, Key=latest_key)
    content = obj['Body'].read().decode('utf-8')
    record = json.loads(content)
    return record

# Initialize or load patient data in session state
if "patients" not in st.session_state:
    st.session_state.patients = [
        {
            "id": "AB",
            "note_type": "Consult",
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

# Sidebar: Active Patients List and Add New Patient
st.sidebar.title("Active Patients")
patient_options = [
    f"{p['id']} - {p['note_type']} - {p['reason']}" for p in st.session_state.patients
]
selected_patient = st.sidebar.selectbox("Select a patient", patient_options, key="patient_select")

st.sidebar.markdown("---")
st.sidebar.subheader("Add New Patient")
new_patient_id = st.sidebar.text_input("Patient ID/Initials", key="new_id")
new_reason = st.sidebar.text_input("Reason for Consult", key="new_reason")
new_note_type = st.sidebar.selectbox("Note Type", ["Consult", "Progress"], key="new_note_type")
if st.sidebar.button("Add Patient", key="add_patient"):
    if new_patient_id and new_reason:
        new_patient = {
            "id": new_patient_id,
            "note_type": new_note_type,
            "reason": new_reason,
            "consultation_note": "",
            "soap_note": "",
            "last_updated": str(datetime.datetime.now())
        }
        st.session_state.patients.append(new_patient)
        st.sidebar.success(f"Patient {new_patient_id} added successfully!")
        st.experimental_rerun()
    else:
        st.sidebar.error("Please enter both Patient ID and Reason for Consult.")

if selected_patient:
    selected_id = selected_patient.split(" - ")[0]
    patient_record = next((p for p in st.session_state.patients if p["id"] == selected_id), None)
    st.session_state.current_patient = patient_record

    st.header(f"Patient {patient_record['id']} - {patient_record['note_type']}")
    st.write(f"**Reason for Consult:** {patient_record['reason']}")
    st.write(f"**Last Updated:** {patient_record.get('last_updated', 'N/A')}")

    # Button to load the latest record from S3 for this patient
    if st.button("Load Latest Patient Record from S3", key="load_s3"):
        loaded_record = load_latest_patient_record_from_s3(patient_record['id'])
        if loaded_record:
            st.session_state.current_patient = loaded_record
            patient_record.update(loaded_record)
            st.success("Patient record loaded from S3.")
            st.json(patient_record)
        else:
            st.info("No record found in S3 for this patient.")

    # Create tabs for Consultation Note, SOAP Note, and Follow-Up Update
    tab1, tab2, tab3 = st.tabs(["Consultation Note", "SOAP Note", "Follow-Up Update"])

    with tab1:
        st.subheader("Generate Consultation Note")
        reason = st.text_input("Reason for Consultation:", patient_record["reason"], key="reason_input")
        symptoms = st.text_area("Presenting Symptoms:", "", height=80, key="symptoms")
        context_history = st.text_area("Clinical History & Context:", "", height=80, key="context")
        labs = st.text_area("Labs:", "", height=80, key="labs")
        assessment_plan_input = st.text_area(
            "Assessment & Plan:",
            "Enter a combined list of problem headings and corresponding treatment options.\n"
            "For example:\n"
            "AKI: Optimize fluid management, avoid nephrotoxic agents, consider RRT if indicated.\n"
            "Metabolic Acidosis: Monitor acid-base status, administer bicarbonate if pH < 7.2.\n"
            "Cardiogenic Shock: Adjust pressor support and collaborate with cardiology.",
            height=150,
            key="assessment_input"
        )
        if st.button("Generate Consultation Note", key="generate_consult"):
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
                generated_note = generator(prompt, max_length=1200, temperature=0.7)[0]["generated_text"].strip()
                generated_note = remove_leading_asterisks(generated_note)
                patient_record["consultation_note"] = generated_note
                patient_record["note_type"] = "Consult"
                patient_record["last_updated"] = str(datetime.datetime.now())
                st.success("Consultation note generated and saved!")
                st.text_area("Consultation Note:", value=generated_note, height=400, key="consult_note_display")

    with tab2:
        st.subheader("Generate SOAP Note")
        case_update = st.text_area("Case Update:", "Enter a comprehensive update on the case", height=150, key="case_update_input")
        if st.button("Generate SOAP Note", key="generate_soap"):
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
                    soap_note = generator(soap_prompt, max_length=800, temperature=0.7)[0]["generated_text"].strip()
                    soap_note = remove_leading_asterisks(soap_note)
                    patient_record["soap_note"] = soap_note
                    patient_record["note_type"] = "Progress"
                    patient_record["last_updated"] = str(datetime.datetime.now())
                    st.success("SOAP note generated and saved!")
                    st.text_area("SOAP Note:", value=soap_note, height=400, key="soap_note_display")

    with tab3:
        st.subheader("Generate Follow-Up Update")
        new_update = st.text_area("Enter New Update:", "Provide a one-liner update...", height=68, key="new_update_input")
        if st.button("Generate Follow-Up Note", key="generate_followup"):
            if patient_record.get("soap_note"):
                base_note = patient_record.get("soap_note")
            else:
                base_note = patient_record.get("consultation_note")
            followup_prompt = f"""
Using the following previous note and a new update, generate an updated follow-up SOAP note for a progress note in the style of a board-certified nephrologist.

Previous Note:
{base_note}

New Update:
{new_update}

Generate an updated SOAP note that integrates the new subjective information with the existing assessment and plan.
"""
            with st.spinner("Generating Follow-Up Note..."):
                new_soap_note = generator(followup_prompt, max_length=800, temperature=0.7)[0]["generated_text"].strip()
                new_soap_note = remove_leading_asterisks(new_soap_note)
                patient_record["soap_note"] = new_soap_note
                patient_record["note_type"] = "Progress"
                patient_record["last_updated"] = str(datetime.datetime.now())
                st.success("Follow-Up note generated and saved!")
                st.text_area("Updated Follow-Up SOAP Note:", value=new_soap_note, height=400, key="followup_display")

    if st.button("Save Patient Record to S3", key="save_patient_record"):
        upload_patient_record_to_s3(patient_record)
        st.json(patient_record)
