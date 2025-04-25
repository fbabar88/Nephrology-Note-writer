import streamlit as st
import openai
import json
import datetime

# Secure your API key in .streamlit/secrets.toml:
# OPENAI_API_KEY = "your_api_key_here"

# Configure OpenAI API
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Initialize session state variables if not present
if 'current_generated_note' not in st.session_state:
    st.session_state.current_generated_note = ""
if 'current_soap_note' not in st.session_state:
    st.session_state.current_soap_note = ""
if 'dataset_entries' not in st.session_state:
    st.session_state.dataset_entries = []

st.title("AI Note Writer for Nephrology Consultations")

##############################################
# Section 0: Style Template Input
##############################################

st.header("0. Note Style Configuration")
style_template = st.text_area(
    "Style Guidelines / Template:",
    """
- **HPI**: 2–3 concise sentences covering age, timeline, key events, and labs.
- **Assessment & Plan** for each problem:
  1. **Problem Name**: One-line explanation with supporting data.
  2. Bullet list of actions (no parentheses), each on its own line.
""",
    height=100
)

##############################################
# Section 1: Generate Consultation Note
##############################################

st.header("1. Generate Consultation Note")

reason = st.text_input("Reason for Consultation:", "")
symptoms = st.text_area("Presenting Symptoms:", "", height=80)
context_history = st.text_area("Clinical History & Context:", "", height=80)
labs = st.text_area("Labs:", "", height=80)
assessment_plan_input = st.text_area(
    "Assessment & Plan:",
    "Enter problem headings and treatment options, e.g.:\n"
    "AKI on CKD III: Creatinine 4.2 suggests contrast injury; optimize fluids, monitor labs.\n"
    "Metabolic Acidosis: Bicarb 20 due to AKI; monitor values, consider supplementation.\n",
    height=150
)

if st.button("Generate Consultation Note"):
    prompt = f"""
Apply these style rules:
{style_template}

Generate a comprehensive Epic consultation note:

**Reason for Consultation:**
{reason}

**HPI:**
{symptoms} {context_history} Labs: {labs}

**Assessment & Plan:**
{assessment_plan_input}

"""
    with st.spinner("Generating Consultation Note..."):
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a nephrology AI assistant for structured notes."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1200,
            temperature=0.5,
        )
        generated_note = response.choices[0].message.content.strip()
        st.session_state.current_generated_note = generated_note
        st.text_area("Consultation Note:", value=generated_note, height=400)

##############################################
# Section 2: Generate SOAP Note with Case Update
##############################################

st.header("2. Generate SOAP Note from Consultation Note with Case Update")
case_update = st.text_area("Case Update:", "Enter a comprehensive update on the case", height=150)

if st.button("Generate SOAP Note"):
    if not st.session_state.current_generated_note:
        st.error("Please generate a consultation note first.")
    else:
        soap_prompt = f"""
Apply these style rules:
{style_template}

Using the consultation note and case update, generate a SOAP note (omit Objective):

Consultation Note:
{st.session_state.current_generated_note}

Case Update:
{case_update}

SOAP Note:
"""
        with st.spinner("Generating SOAP Note..."):
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a nephrology AI assistant for structured SOAP notes."},
                    {"role": "user", "content": soap_prompt}
                ],
                max_tokens=800,
                temperature=0.7,
            )
            soap_note = response.choices[0].message.content.strip()
            st.session_state.current_soap_note = soap_note
            st.text_area("SOAP Note:", value=soap_note, height=400)

##############################################
# Section 3: Dataset Collection for Fine-Tuning
##############################################

st.header("3. Dataset Collection for Fine-Tuning")

if st.button("Save Entry to Dataset"):
    entry = {
        "style_guidelines": style_template,
        "reason_for_consultation": reason,
        "presenting_symptoms": symptoms,
        "clinical_history_context": context_history,
        "labs": labs,
        "assessment_plan_input": assessment_plan_input,
        "consultation_note": st.session_state.current_generated_note,
        "case_update": case_update,
        "soap_note": st.session_state.current_soap_note,
        "timestamp": str(datetime.datetime.now())
    }
    st.session_state.dataset_entries.append(entry)
    with open("dataset_entries.jsonl", "a") as f:
        json.dump(entry, f)
        f.write("\n")
    st.success("Entry saved to dataset!")

if st.button("Download Dataset"):
    dataset_jsonl = "\n".join([json.dumps(entry) for entry in st.session_state.dataset_entries])
    st.download_button(label="Download Dataset", data=dataset_jsonl,
                       file_name="fine_tuning_dataset.jsonl", mime="text/plain")

