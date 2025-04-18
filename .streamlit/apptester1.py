import os
os.environ["STREAMLIT_WATCH_FILES"] = "false"

import streamlit as st
import openai
import boto3
import json
import datetime
import re

# ─── Configuration ───────────────────────────────────────────────────────────────
openai.api_key = st.secrets.get("OPENAI_API_KEY", "")
model_name = st.sidebar.selectbox(
    "Choose model", ["gpt-3.5-turbo", "gpt-4"], index=1
)

# ─── Helpers ────────────────────────────────────────────────────────────────────
def remove_leading_asterisks(text: str) -> str:
    return "\n".join([re.sub(r"^\s*\*\s*", "", line) for line in text.splitlines()])

# ─── AWS S3 Integration ─────────────────────────────────────────────────────────
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
    timestamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    key = f"patients/{record['id']}_{timestamp}.json"
    s3.put_object(Body=json.dumps(record), Bucket=bucket, Key=key)
    st.success(f"Saved to S3: {key}")

# ─── Session State ─────────────────────────────────────────────────────────────
if "patients" not in st.session_state:
    st.session_state.patients = []
if "current_patient" not in st.session_state:
    st.session_state.current_patient = None

# ─── Sidebar: Patients ──────────────────────────────────────────────────────────
st.sidebar.title("Patients")
options = [f"{p['id']} - {p['note_type']} - {p['reason']}" for p in st.session_state.patients]
sel = st.sidebar.selectbox("Select a patient", options, key="patient_select")

st.sidebar.markdown("---")
st.sidebar.subheader("Add New Patient")
id_in = st.sidebar.text_input("ID/Initials", key="new_id")
reason_in = st.sidebar.text_input("Reason", key="new_reason")
type_in = st.sidebar.selectbox("Note Type", ["Consult","Progress"], key="new_type")
if st.sidebar.button("Add"):  
    if id_in and reason_in:
        st.session_state.patients.append({
            "id": id_in,
            "note_type": type_in,
            "reason": reason_in,
            "consultation_note": "",
            "soap_note": "",
            "last_updated": str(datetime.datetime.now())
        })
        st.experimental_rerun()
    else:
        st.sidebar.error("Enter both ID and reason.")

# ─── Main ───────────────────────────────────────────────────────────────────────
if sel:
    pid = sel.split(" - ")[0]
    record_idx = next(i for i,p in enumerate(st.session_state.patients) if p["id"]==pid)
    record = st.session_state.patients[record_idx]
    st.session_state.current_patient = record

    st.header(f"Patient {record['id']} ({record['note_type']})")
    st.write(f"**Reason:** {record['reason']}")
    st.write(f"**Last Updated:** {record['last_updated']}")

    tab1,tab2,tab3 = st.tabs(["Consultation Note","SOAP Note","Follow-Up"])

    with tab1:
        st.subheader("Generate Consultation Note")
        reason = st.text_input("Reason for Consultation:", record.get("reason", ""), key=f"reason_{pid}")
        symptoms = st.text_area("Presenting Symptoms:", key=f"sym_{pid}")
        context_history = st.text_area("Clinical History & Context:", key=f"hist_{pid}")
        labs = st.text_area("Labs:", key=f"labs_{pid}")
        assessment_plan_input = st.text_area(
            "Assessment & Plan (Targeted):",
            key=f"ap_{pid}"
        )

        if st.button("Generate Consultation Note", key=f"gen1_{pid}"):
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
1. Reason for Consultation: Restate the consultation reason.
2. History of Present Illness (HPI): Provide a concise narrative summarizing the presenting symptoms, clinical history & context, and labs.
3. Assessment: List each problem mentioned in the 'Assessment & Plan' input as a heading.
4. Plan: Consolidate all treatment recommendations into a single bullet-point list at the end of the note without any subheadings.

Do not add any extra summary sections.
"""
            with st.spinner("Generating Consultation Note..."):
                resp = openai.ChatCompletion.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "You are a board-certified nephrologist writing an Epic-style consultation note."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1200,
                    temperature=0.5
                )
            generated_note = remove_leading_asterisks(resp.choices[0].message.content)
            record.update({
                "consultation_note": generated_note,
                "note_type": "Consult",
                "last_updated": str(datetime.datetime.now())
            })
            st.session_state.patients[record_idx] = record
            st.experimental_rerun()

        if record.get("consultation_note"):
            st.subheader("Consultation Note")
            st.text_area("", record["consultation_note"], height=300)
            st.download_button(
                "Download as .txt",
                record["consultation_note"],
                file_name=f"{record['id']}_consult.txt",
                mime="text/plain"
            )

    with tab2:
        st.subheader("Generate SOAP Note")
        update = st.text_area("Case Update:", key=f"upd_{pid}")
        if st.button("Generate SOAP Note", key=f"gen2_{pid}"):
            if not record.get("consultation_note"):
                st.error("Generate consult note first.")
            else:
                prompt = f"Consultation Note:\n{record['consultation_note']}\n\nCase Update:\n{update}"
                with st.spinner("Generating SOAP Note..."):
                    resp = openai.ChatCompletion.create(
                        model=model_name,
                        messages=[
                            {"role":"system","content":"You are a nephrologist drafting a SOAP progress note."},
                            {"role":"user","content":prompt}
                        ],
                        max_tokens=800,
                        temperature=0.5
                    )
                soap = remove_leading_asterisks(resp.choices[0].message.content)
                record.update({"soap_note": soap, "note_type": "Progress", "last_updated": str(datetime.datetime.now())})
                st.session_state.patients[record_idx] = record
                st.experimental_rerun()

    with tab3:
        st.subheader("Generate Follow-Up")
        one = st.text_area("One-line update:", key=f"one_{pid}")
        if st.button("Generate Follow-Up", key=f"gen3_{pid}"):
            base = record.get("soap_note") or record.get("consultation_note")
            prompt = (
                f"You are a board-certified nephrologist updating a follow-up SOAP note with these instructions:\n"
                f"- In the Subjective section, include only a concise one-liner summarizing the new update.\n"
                f"- Do not repeat the full history of present illness.\n"
                f"- In the Assessment and Plan section, integrate the new update with the existing plan.\n\n"
                f"Previous Note:\n{base}\n\nNew Update (one-line):\n{one}\n"
            )
            with st.spinner("Generating Follow-Up Note..."):
                resp = openai.ChatCompletion.create(
                    model=model_name,
                    messages=[
                        {"role":"system","content":"You are a nephrologist updating a follow-up SOAP note."},
                        {"role":"user","content":prompt}
                    ],
                    max_tokens=600,
                    temperature=0.5
                )
            new = remove_leading_asterisks(resp.choices[0].message.content)
            record.update({"soap_note": new, "note_type": "Progress", "last_updated": str(datetime.datetime.now())})
            st.session_state.patients[record_idx] = record
            st.experimental_rerun()

    if st.button("Save to S3", key=f"save_{pid}"):
        upload_patient_record_to_s3(record)
