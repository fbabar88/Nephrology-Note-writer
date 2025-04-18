import os
os.environ["STREAMLIT_WATCH_FILES"] = "false"

import streamlit as st
import openai
import boto3
import json
import datetime
import re

# ─── Configuration ───────────────────────────────────────────────────────────────

# Use your OpenAI API key (set in Streamlit secrets as OPENAI_API_KEY)
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Optionally let the user choose model in the sidebar:
model_name = st.sidebar.selectbox(
    "Choose model",
    ["gpt-3.5-turbo", "gpt-4"],
    index=1
)

# ─── Helpers ────────────────────────────────────────────────────────────────────

def remove_leading_asterisks(text: str) -> str:
    cleaned = [re.sub(r"^\s*\*\s*", "", line) for line in text.splitlines()]
    return "\n".join(cleaned)

def get_s3_client():
    return boto3.client(
        's3',
        aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
        region_name=st.secrets["AWS_DEFAULT_REGION"]
    )

def upload_patient_record_to_s3(record):
    s3 = get_s3_client()
    bucket = st.secrets["BUCKET_NAME"]
    ts = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    key = f"patients/{record['id']}_{ts}.json"
    s3.put_object(Body=json.dumps(record), Bucket=bucket, Key=key)
    st.success(f"Saved to S3: {key}")

def load_latest_patient_record_from_s3(patient_id):
    s3 = get_s3_client()
    bucket = st.secrets["BUCKET_NAME"]
    prefix = f"patients/{patient_id}_"
    resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    if 'Contents' not in resp:
        st.warning("No S3 records found.")
        return None
    latest = sorted(resp['Contents'], key=lambda o: o['LastModified'], reverse=True)[0]
    obj = s3.get_object(Bucket=bucket, Key=latest['Key'])
    return json.loads(obj['Body'].read().decode())

def list_patient_records_from_s3(patient_id):
    s3 = get_s3_client()
    bucket = st.secrets["BUCKET_NAME"]
    prefix = f"patients/{patient_id}_"
    resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    records = []
    if 'Contents' in resp:
        for o in resp['Contents']:
            label = f"{o['Key']} ({o['LastModified'].strftime('%Y-%m-%d %H:%M:%S')})"
            records.append((label, o['Key']))
    return records

# ─── Session State Initialization ───────────────────────────────────────────────

if "patients" not in st.session_state:
    st.session_state.patients = [
        {"id":"AB","note_type":"Consult","reason":"AKI secondary to hypovolemia","consultation_note":"","soap_note":"","last_updated":str(datetime.datetime.now())},
        {"id":"CD","note_type":"Progress","reason":"Follow-up on AKI and fluid management","consultation_note":"","soap_note":"","last_updated":str(datetime.datetime.now())},
    ]

if "current_patient" not in st.session_state:
    st.session_state.current_patient = None

# ─── Sidebar: Patient Management ────────────────────────────────────────────────

st.sidebar.title("Patients")
options = [f"{p['id']} – {p['note_type']} – {p['reason']}" for p in st.session_state.patients]
sel = st.sidebar.selectbox("Select a patient", options, key="patient_select")

st.sidebar.markdown("---")
st.sidebar.subheader("Add New Patient")
new_id = st.sidebar.text_input("ID/Initials", key="new_id")
new_reason = st.sidebar.text_input("Reason", key="new_reason")
new_type = st.sidebar.selectbox("Type", ["Consult","Progress"], key="new_note_type")
if st.sidebar.button("Add"):
    if new_id and new_reason:
        st.session_state.patients.append({
            "id": new_id, "note_type": new_type, "reason": new_reason,
            "consultation_note":"", "soap_note":"", "last_updated":str(datetime.datetime.now())
        })
        st.experimental_rerun()
    else:
        st.sidebar.error("Enter both ID and reason.")

# ─── Main Area ─────────────────────────────────────────────────────────────────

if sel:
    pid = sel.split(" – ")[0]
    record = next(p for p in st.session_state.patients if p["id"] == pid)
    st.session_state.current_patient = record

    st.header(f"Patient {record['id']} ({record['note_type']})")
    st.write(f"**Reason:** {record['reason']}")
    st.write(f"**Last Updated:** {record.get('last_updated')}")

    # Load from S3
    if st.button("Load Latest from S3"):
        loaded = load_latest_patient_record_from_s3(pid)
        if loaded:
            record.update(loaded)
            st.success("Loaded latest record.")
            st.json(record)

    # Choose specific S3 record
    recs = list_patient_records_from_s3(pid)
    if recs:
        st.markdown("#### Load Specific Saved Record")
        labels = [lbl for lbl, _ in recs]
        choice = st.selectbox("Which record?", labels, key="select_record")
        if st.button("Load Selected"):
            key = next(k for lbl,k in recs if lbl==choice)
            obj = get_s3_client().get_object(Bucket=st.secrets["BUCKET_NAME"], Key=key)
            loaded = json.loads(obj['Body'].read().decode())
            record.update(loaded)
            st.success("Loaded selected record.")
            st.json(record)

    tab1, tab2, tab3 = st.tabs(["Consultation Note","SOAP Note","Follow‑Up"])

    # ── Tab 1: Consultation Note ───────────────────────────────
    with tab1:
        st.subheader("Generate Consultation Note")
        reason = st.text_input("Reason:", record["reason"], key="reason_input")
        symptoms = st.text_area("Symptoms:", "", height=80, key="symptoms")
        history = st.text_area("History/Context:", "", height=80, key="context")
        labs = st.text_area("Labs:", "", height=80, key="labs")
        assessment = st.text_area(
            "Assessment & Plan (one per line):",
            "AKI: Optimize fluids…\nMetabolic Acidosis: …",
            height=150, key="assessment_input"
        )
        if st.button("Generate Consultation Note", key="gen_consult"):
            prompt = f"""
Reason: {reason}

Symptoms: {symptoms}

History/Context: {history}

Labs: {labs}

Assessment & Plan:
{assessment}
"""
            with st.spinner("Generating…"):
                resp = openai.ChatCompletion.create(
                    model=model_name,
                    messages=[
                        {"role":"system","content":"You are a board-certified nephrologist writing an Epic-style consultation note."},
                        {"role":"user","content":prompt}
                    ],
                    max_tokens=1200,
                    temperature=0.5
                )
                note = remove_leading_asterisks(resp.choices[0].message.content.strip())
                record["consultation_note"] = note
                record["note_type"] = "Consult"
                record["last_updated"] = str(datetime.datetime.now())
                st.success("Consultation note generated.")
                st.text_area("Consultation Note:", note, height=400, key="consult_display")

        default_ros_pe = """**Review of Systems:** …  
**Physical Exam:** …"""
        st.text_area("ROS & PE Template:", default_ros_pe, height=300, key="ros_pe_initial")

    # ── Tab 2: SOAP Note ──────────────────────────────────────
    with tab2:
        st.subheader("Generate SOAP Note")
        update_txt = st.text_area("Case Update:", "Enter update here", height=150, key="case_update_input")
        if st.button("Generate SOAP Note", key="gen_soap"):
            if not record.get("consultation_note"):
                st.error("Generate consult note first.")
            else:
                soap_prompt = f"""
Consultation Note:
{record['consultation_note']}

Case Update:
{update_txt}
"""
                with st.spinner("Generating…"):
                    resp = openai.ChatCompletion.create(
                        model=model_name,
                        messages=[
                            {"role":"system","content":"You are a nephrologist drafting a SOAP progress note."},
                            {"role":"user","content":soap_prompt}
                        ],
                        max_tokens=800,
                        temperature=0.5
                    )
                    soap = remove_leading_asterisks(resp.choices[0].message.content.strip())
                    record["soap_note"] = soap
                    record["note_type"] = "Progress"
                    record["last_updated"] = str(datetime.datetime.now())
                    st.success("SOAP note generated.")
                    st.text_area("SOAP Note:", soap, height=400, key="soap_display")

    # ── Tab 3: Follow‑Up Update ────────────────────────────────
    with tab3:
        st.subheader("Generate Follow‑Up Update")
        one_liner = st.text_area("One‑line update:", "Enter update...", height=80, key="new_update_input")
        if st.button("Generate Follow‑Up", key="gen_followup"):
            base = record.get("soap_note") or record.get("consultation_note")
            followup_prompt = f"""
Previous Note:
{base}

One‑liner Update:
{one_liner}
"""
            with st.spinner("Generating…"):
                resp = openai.ChatCompletion.create(
                    model=model_name,
                    messages=[
                        {"role":"system","content":"You are a nephrologist updating a follow‑up SOAP note based on a one‑liner."},
                        {"role":"user","content":followup_prompt}
                    ],
                    max_tokens=600,
                    temperature=0.5
                )
                new_soap = remove_leading_asterisks(resp.choices[0].message.content.strip())
                record["soap_note"] = new_soap
                record["note_type"] = "Progress"
                record["last_updated"] = str(datetime.datetime.now())
                st.success("Follow‑up note generated.")
                st.text_area("Updated SOAP Note:", new_soap, height=400, key="followup_display")

    # ── Save Back to S3 ───────────────────────────────────────
    if st.button("Save to S3", key="save_patient_record"):
        upload_patient_record_to_s3(record)
        st.json(record)
