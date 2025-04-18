import os
os.environ["STREAMLIT_WATCH_FILES"] = "false"

import streamlit as st
import openai
import json
import datetime
import re

# ─── Configuration ───────────────────────────────────────────────────────────────

# Use your OpenAI API key from Streamlit secrets as OPENAI_API_KEY
# In .streamlit/secrets.toml:
# OPENAI_API_KEY = "sk-your-openai-api-key-here"
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Optionally let the user choose model in the sidebar:
model_name = st.sidebar.selectbox(
    "Choose model", ["gpt-3.5-turbo", "gpt-4"], index=1
)

# ─── Helpers ────────────────────────────────────────────────────────────────────

def remove_leading_asterisks(text: str) -> str:
    return "\n".join([re.sub(r"^\s*\*\s*", "", line) for line in text.splitlines()])

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

    tab1, tab2, tab3 = st.tabs(["Consultation Note","SOAP Note","Follow‑Up"])

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
Reason: {reason}\n\nSymptoms: {symptoms}\n\nHistory/Context: {history}\n\nLabs: {labs}\n\nAssessment & Plan:\n{assessment}\n"""
            with st.spinner("Generating…"):
                resp = openai.ChatCompletion.create(
                    model=model_name,
                    messages=[
                        {"role":"system","content":"You are a board-certified nephrologist writing an Epic-style consultation note."},
                        {"role":"user","content":prompt}
                    ], max_tokens=1200, temperature=0.5
                )
                note = remove_leading_asterisks(resp.choices[0].message.content)
                record.update({"consultation_note":note, "note_type":"Consult", "last_updated":str(datetime.datetime.now())})
                st.success("Consultation note generated.")
                st.text_area("Consultation Note:", note, height=400, key="consult_display")

        default_ros_pe = """**Review of Systems:** …  \n**Physical Exam:** …"""
        st.text_area("ROS & PE Template:", default_ros_pe, height=300, key="ros_pe_initial")

    with tab2:
        st.subheader("Generate SOAP Note")
        update_txt = st.text_area("Case Update:", "Enter update here", height=150, key="case_update_input")
        if st.button("Generate SOAP Note", key="gen_soap"):
            if not record.get("consultation_note"):
                st.error("Generate consult note first.")
            else:
                soap_prompt = f"""Consultation Note:\n{record['consultation_note']}\n\nCase Update:\n{update_txt}"""
                with st.spinner("Generating…"):
                    resp = openai.ChatCompletion.create(
                        model=model_name,
                        messages=[
                            {"role":"system","content":"You are a nephrologist drafting a SOAP progress note."},
                            {"role":"user","content":soap_prompt}
                        ], max_tokens=800, temperature=0.5
                    )
                    soap = remove_leading_asterisks(resp.choices[0].message.content)
                    record.update({"soap_note":soap, "note_type":"Progress", "last_updated":str(datetime.datetime.now())})
                    st.success("SOAP note generated.")
                    st.text_area("SOAP Note:", soap, height=400, key="soap_display")

    with tab3:
        st.subheader("Generate Follow‑Up Update")
        one_liner = st.text_area("One‑line update:", "Enter update...", height=80, key="new_update_input")
        if st.button("Generate Follow‑up", key="gen_followup"):
            base = record.get("soap_note") or record.get("consultation_note")
            followup_prompt = f"""Previous Note:\n{base}\n\nOne‑liner Update:\n{one_liner}"""
            with st.spinner("Generating…"):
                resp = openai.ChatCompletion.create(
                    model=model_name,
                    messages=[
                        {"role":"system","content":"You are a nephrologist updating a follow‑up SOAP note based on a one‑liner."},
                        {"role":"user","content":followup_prompt}
                    ], max_tokens=600, temperature=0.5
                )
                new_soap = remove_leading_asterisks(resp.choices[0].message.content)
                record.update({"soap_note":new_soap, "note_type":"Progress", "last_updated":str(datetime.datetime.now())})
                st.success("Follow‑up note generated.")
                st.text_area("Updated SOAP Note:", new_soap, height=400, key="followup_display")

# AWS storage integration is deactivated for now.
