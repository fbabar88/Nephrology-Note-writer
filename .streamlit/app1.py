import streamlit as st
import openai
import json
import datetime

# Configure the OpenAI SDK for DeepSeek (Beta Endpoint)
openai.api_base = "https://api.deepseek.com/beta"  # Use the beta endpoint
openai.api_key = st.secrets.get("DEEPSEEK_API_KEY", "")  # Ensure your API key is added in Streamlit secrets

# Initialize session state variables if not present
if 'current_generated_note' not in st.session_state:
    st.session_state.current_generated_note = ""
if 'current_soap_note' not in st.session_state:
    st.session_state.current_soap_note = ""
if 'dataset_entries' not in st.session_state:
    st.session_state.dataset_entries = []

st.title("AI Note Writer for Nephrology Consultations")

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
        st.session_state.current_generated_note = generated_note
        st.text_area("Consultation Note:", value=generated_note, height=400)

##############################################
# Section 2: Generate SOAP Note from Consultation Note with Case Update
##############################################

st.header("2. Generate SOAP Note from Consultation Note with Case Update")
case_update = st.text_area("Case Update:", "Enter a comprehensive update on the case", height=150)

if st.button("Generate SOAP Note"):
    if not st.session_state.current_generated_note:
        st.error("Please generate a consultation note first.")
    else:
        soap_prompt = f"""
Using the following consultation note and case update, generate a SOAP note for a progress note in the style of a board-certified nephrologist.
In the SOAP note:
- **Subjective:** Provide a concise statement of the patient's current condition using the case update.
- **Assessment and Plan:** Reflect the problem list and treatment options as provided in the consultation note.
- **Objective:** Omit this section.

Consultation Note:
{st.session_state.current_generated_note}

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
            st.session_state.current_soap_note = soap_note
            st.text_area("SOAP Note:", value=soap_note, height=400)

##############################################
# Section 3: Dataset Collection for Fine-Tuning
##############################################

st.header("3. Dataset Collection for Fine-Tuning")

if st.button("Save Entry to Dataset"):
    entry = {
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
    # Append the entry to a file for persistence
    with open("dataset_entries.jsonl", "a") as f:
        json.dump(entry, f)
        f.write("\n")
    st.success("Entry saved to dataset!")

if st.button("Download Dataset"):
    # Combine dataset entries into JSONL format for download
    dataset_jsonl = "\n".join([json.dumps(entry) for entry in st.session_state.dataset_entries])
    st.download_button(label="Download Dataset", data=dataset_jsonl,
                       file_name="fine_tuning_dataset.jsonl", mime="text/plain")
