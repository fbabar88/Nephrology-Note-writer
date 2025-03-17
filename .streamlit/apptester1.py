import streamlit as st
import openai
import boto3
import json
import datetime
import tempfile

# Configure OpenAI SDK for DeepSeek (Beta Endpoint)
openai.api_base = "https://api.deepseek.com/beta"
openai.api_key = st.secrets.get("DEEPSEEK_API_KEY", "")

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
    # Create a unique key for the record using patient ID and current timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    file_key = f"patients/{record['id']}_{timestamp}.json"
    # Convert the record to JSON string
    record_json = json.dumps(record)
    # Upload the JSON string to S3
    s3.put_object(Body=record_json, Bucket=bucket, Key=file_key)
    st.success(f"Patient record saved to S3 with key: {file_key}")

# Initialize or load patient data in session state
if "patients" not in st.session_state:
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

# Sidebar: Active Patients List and Add New Patient
st.sidebar.title("Active Patients")

# Display active patient list
patient_options = [
    f"{p['id']} - {p['note_type']} - {p['reason']}" for p in st.session_state.patients
]
selected_patient = st.sidebar.selectbox("Select a patient", patient_options)

# Add New Patient Section
st.sidebar.markdown("---")
st.sidebar.subheader("Add New Patient")
new_patient_id = st.sidebar.text_input("Patient ID/Initials", key="new_id")
new_reason = st.sidebar.text_input("Reason for Consult", key="new_reason")
new_note_type = st.sidebar.selectbox("Note Type", ["Consult", "Progress"], key="new_note_type")
if st.sidebar.button("Add Patient"):
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
        st.sidebar.success(f"Patient {new_patient_id} 
