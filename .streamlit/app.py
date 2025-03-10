import streamlit as st
import openai
import datetime
import time
import requests  # For fetching external guidelines

# --------------------------
# Configure the DeepSeek API
# --------------------------
openai.api_base = "https://api.deepseek.com/v1"  # Using the v1 endpoint
openai.api_key = st.secrets.get("DEEPSEEK_API_KEY", "YOUR_API_KEY")

# --------------------------
# Function to fetch guideline data from external API
# --------------------------
def fetch_guidelines(condition):
    """
    Fetch guideline text for a given condition from an external API.
    Replace the URL and parameters with your actual guidelines API details.
    """
    # Example URL – change to your actual endpoint.
    url = f"https://example-guidelines-api.com/guidelines?condition={condition}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Assume the API returns a JSON with a key "guideline_text"
            return data.get("guideline_text", "")
        else:
            return ""
    except Exception as e:
        st.error(f"Error fetching guidelines for {condition}: {e}")
        return ""

# --------------------------
# Title, Global Timer, and Visit Type
# --------------------------
st.title("Nephrology Note Generator - Multi-Condition Interface")

# Sidebar: Timer and Visit Type
if st.sidebar.button("Start Timer"):
    st.session_state.start_time = time.time()
    st.sidebar.write("Timer started!")

if "start_time" in st.session_state:
    elapsed = time.time() - st.session_state.start_time
    st.sidebar.write(f"Time since start: {elapsed:.2f} seconds")

# Global visit type for non-CKD conditions (set via sidebar)
visit_type = st.sidebar.radio("Select Visit Type", options=["New Patient", "Follow-Up"], key="visit_type")
st.sidebar.write("Selected Visit Type:", visit_type)

# Get today's date
visit_date = datetime.date.today().strftime("%B %d, %Y")

# --------------------------
# Create Tabs for Different Conditions
# --------------------------
tab_labels = [
    "CKD Evaluation (New Patient)",
    "CKD Follow-Up",
    "Hypertension (HTN)",
    "Glomerulonephritis",
    "Hyponatremia",
    "Hypokalemia",
    "Proteinuria & Hematuria",
    "Renal Cyst"
]
tabs = st.tabs(tab_labels)

# --------------------------
# Tab 1: CKD Evaluation (New Patient)
# --------------------------
with tabs[0]:
    st.header("CKD Evaluation (New Patient)")
    reason_for_visit = st.text_input("Reason for Visit", "CKD Evaluation", key="ckd_eval_reason")
    symptoms = st.text_area("Symptoms", "Enter patient's symptoms...", key="ckd_eval_symptoms")
    risk_factors = st.text_area("Risk Factors (e.g., NSAIDs, DM, HTN, other nephrotoxins)", "Enter risk factors...", key="ckd_eval_risk_factors")
    dm_status = st.text_input("Diabetes Mellitus Status", "Present/Absent", key="ckd_eval_dm_status")
    htn_status = st.text_input("Hypertension Status", "Present/Absent", key="ckd_eval_htn_status")
    labs = st.text_area("Lab Data", "Enter relevant lab data...", key="ckd_eval_labs")
    assessment_plan = st.text_area("Assessment & Plan", "Enter assessment and plan...", key="ckd_eval_assessment_plan")
    
    if st.button("Generate Note for CKD Evaluation", key="ckd_eval_generate"):
        elapsed = time.time() - st.session_state.get("start_time", time.time())
        st.write(f"Time taken to input variables: {elapsed:.2f} seconds")
        # Fetch guidelines for CKD Evaluation
        guidelines = fetch_guidelines("CKD Evaluation")
        prompt = f"""
Visit Date: {visit_date}
Reason for Visit: {reason_for_visit}
[New Patient - CKD Evaluation]

Subjective:
Patient presents with the following symptoms: {symptoms}.

Risk Factors:
{risk_factors}

Additional Info:
DM Status: {dm_status}, HTN Status: {htn_status}.

Lab Data:
{labs}

Assessment & Plan:
{assessment_plan}

Guideline Recommendations:
{guidelines}

Generate a comprehensive SOAP note focusing on the Subjective and Assessment & Plan sections for a new patient CKD evaluation.
"""
        st.code(prompt, language="plaintext")
        with st.spinner("Calling DeepSeek API..."):
            try:
                response = openai.Completion.create(
                    model="deepseek-chat",
                    prompt=prompt,
                    max_tokens=800,
                    temperature=0.7,
                )
                generated_note = response.choices[0].text.strip()
                st.subheader("Generated Note")
                st.markdown(generated_note)
            except Exception as e:
                st.error(f"API call failed: {e}")

# --------------------------
# Tab 2: CKD Follow-Up
# --------------------------
with tabs[1]:
    st.header("CKD Follow-Up")
    reason_for_visit = st.text_input("Reason for Visit", "CKD Follow-Up", key="ckd_fu_reason")
    symptoms = st.text_area("Symptoms", "Enter current symptoms...", key="ckd_fu_symptoms")
    ckd_stage = st.selectbox("CKD Stage", options=["1", "2", "3", "4", "5"], index=2, key="ckd_fu_stage")
    kidney_trend = st.selectbox("Kidney Function Trend", options=["Improving", "Stable", "Worsening"], key="ckd_fu_trend")
    dm_status = st.text_input("Diabetes Mellitus Status", "Controlled/Uncontrolled", key="ckd_fu_dm_status")
    htn_status = st.text_input("Hypertension Status", "Controlled/Uncontrolled", key="ckd_fu_htn_status")
    labs = st.text_area("Lab Data", "Enter updated lab data...", key="ckd_fu_labs")
    assessment_plan = st.text_area("Assessment & Plan", "Enter assessment and plan...", key="ckd_fu_assessment_plan")
    
    if st.button("Generate Note for CKD Follow-Up", key="ckd_fu_generate"):
        elapsed = time.time() - st.session_state.get("start_time", time.time())
        st.write(f"Time taken to input variables: {elapsed:.2f} seconds")
        guidelines = fetch_guidelines("CKD Follow-Up")
        prompt = f"""
Visit Date: {visit_date}
Reason for Visit: {reason_for_visit}
[Follow-Up - CKD]

Subjective:
Patient presents for follow-up with the following symptoms: {symptoms}.

CKD Details:
Stage: {ckd_stage}, Kidney Function Trend: {kidney_trend}.

Additional Info:
DM Status: {dm_status}, HTN Status: {htn_status}.

Lab Data:
{labs}

Assessment & Plan:
{assessment_plan}

Guideline Recommendations:
{guidelines}

Generate a comprehensive SOAP note focusing on the Subjective and Assessment & Plan sections for a CKD follow-up visit.
"""
        st.code(prompt, language="plaintext")
        with st.spinner("Calling DeepSeek API..."):
            try:
                response = openai.Completion.create(
                    model="deepseek-chat",
                    prompt=prompt,
                    max_tokens=800,
                    temperature=0.7,
                )
                generated_note = response.choices[0].text.strip()
                st.subheader("Generated Note")
                st.markdown(generated_note)
            except Exception as e:
                st.error(f"API call failed: {e}")

# --------------------------
# For non-CKD conditions, use a function to generate note prompts with guidelines.
# --------------------------
def generate_note_with_guidelines(prompt, button_key, condition):
    # Fetch guidelines for the given condition.
    guidelines = fetch_guidelines(condition)
    full_prompt = f"{prompt}\n\nGuideline Recommendations:\n{guidelines}\n"
    st.code(full_prompt, language="plaintext")
    if st.button("Generate Note", key=button_key):
        elapsed = time.time() - st.session_state.get("start_time", time.time())
        st.write(f"Time taken to input variables: {elapsed:.2f} seconds")
        with st.spinner("Calling DeepSeek API..."):
            try:
                response = openai.Completion.create(
                    model="deepseek-chat",
                    prompt=full_prompt,
                    max_tokens=800,
                    temperature=0.7,
                )
                generated_note = response.choices[0].text.strip()
                st.subheader("Generated Note")
                st.markdown(generated_note)
            except Exception as e:
                st.error(f"API call failed: {e}")

# --------------------------
# Tab 3: Hypertension (HTN)
# --------------------------
with tabs[2]:
    st.header("Hypertension (HTN)")
    reason_for_visit = st.text_input("Reason for Visit", "HTN Evaluation/Follow-Up", key="htn_reason")
    if visit_type == "New Patient":
        hpi = st.text_area("HPI", "Enter patient's HPI (symptoms, onset, etc.)", key="htn_hpi")
        labs = st.text_area("Labs", "Enter lab data, if any...", key="htn_labs_new")
        assessment_plan = st.text_area("Assessment & Plan", "Enter assessment and plan for HTN management...", key="htn_ap_new")
        prompt = f"""
Visit Date: {visit_date}
Reason for Visit: {reason_for_visit}
[HTN New Patient Evaluation]

HPI:
{hpi}

Labs:
{labs}

Assessment & Plan:
{assessment_plan}

Generate a note focused on the evaluation of hypertension for a new patient visit.
"""
        generate_note_with_guidelines(prompt, "htn_generate_new", "Hypertension")
    else:
        interval_history = st.text_area("Interval History", "Enter interval history (changes since last visit)...", key="htn_interval")
        labs = st.text_area("Labs", "Enter updated lab data...", key="htn_labs_fu")
        assessment_plan = st.text_area("Assessment & Plan (include Medication Changes)", "Enter assessment, plan, and medication changes...", key="htn_ap_fu")
        prompt = f"""
Visit Date: {visit_date}
Reason for Visit: {reason_for_visit}
[HTN Follow-Up]

Interval History:
{interval_history}

Labs:
{labs}

Assessment & Plan (with integrated Medication Changes):
{assessment_plan}

Generate a note focused on the follow-up evaluation of hypertension, ensuring medication changes are integrated.
"""
        generate_note_with_guidelines(prompt, "htn_generate_fu", "Hypertension")

# --------------------------
# Tab 4: Glomerulonephritis
# --------------------------
with tabs[3]:
    st.header("Glomerulonephritis")
    reason_for_visit = st.text_input("Reason for Visit", "Glomerulonephritis Evaluation/Follow-Up", key="gng_reason")
    if visit_type == "New Patient":
        hpi = st.text_area("HPI", "Enter patient's HPI (symptoms, onset, etc.)", key="gng_hpi")
        labs = st.text_area("Labs", "Enter lab data, if any...", key="gng_labs_new")
        assessment_plan = st.text_area("Assessment & Plan", "Enter assessment and plan for glomerulonephritis...", key="gng_ap_new")
        prompt = f"""
Visit Date: {visit_date}
Reason for Visit: {reason_for_visit}
[Glomerulonephritis New Patient Evaluation]

HPI:
{hpi}

Labs:
{labs}

Assessment & Plan:
{assessment_plan}

Generate a note focused on the evaluation of glomerulonephritis for a new patient visit.
"""
        generate_note_with_guidelines(prompt, "gng_generate_new", "Glomerulonephritis")
    else:
        interval_history = st.text_area("Interval History", "Enter interval history (changes since last visit)...", key="gng_interval")
        labs = st.text_area("Labs", "Enter updated lab data...", key="gng_labs_fu")
        assessment_plan = st.text_area("Assessment & Plan", "Enter assessment and plan for glomerulonephritis...", key="gng_ap_fu")
        prompt = f"""
Visit Date: {visit_date}
Reason for Visit: {reason_for_visit}
[Glomerulonephritis Follow-Up]

Interval History:
{interval_history}

Labs:
{labs}

Assessment & Plan:
{assessment_plan}

Generate a note focused on the follow-up evaluation of glomerulonephritis.
"""
        generate_note_with_guidelines(prompt, "gng_generate_fu", "Glomerulonephritis")

# --------------------------
# Tab 5: Hyponatremia
# --------------------------
with tabs[4]:
    st.header("Hyponatremia")
    reason_for_visit = st.text_input("Reason for Visit", "Hyponatremia Evaluation/Follow-Up", key="hyponat_reason")
    if visit_type == "New Patient":
        hpi = st.text_area("HPI", "Enter patient's HPI (symptoms, onset, etc.)", key="hyponat_hpi")
        labs = st.text_area("Labs", "Enter lab data (serum sodium, osmolality, etc.)", key="hyponat_labs_new")
        assessment_plan = st.text_area("Assessment & Plan", "Enter assessment and plan for hyponatremia...", key="hyponat_ap_new")
        prompt = f"""
Visit Date: {visit_date}
Reason for Visit: {reason_for_visit}
[Hyponatremia New Patient Evaluation]

HPI:
{hpi}

Labs:
{labs}

Assessment & Plan:
{assessment_plan}

Generate a note focused on the evaluation of hyponatremia for a new patient visit.
"""
        generate_note_with_guidelines(prompt, "hyponat_generate_new", "Hyponatremia")
    else:
        interval_history = st.text_area("Interval History", "Enter interval history (changes since last visit)...", key="hyponat_interval")
        labs = st.text_area("Labs", "Enter updated lab data...", key="hyponat_labs_fu")
        assessment_plan = st.text_area("Assessment & Plan (include Medication Changes)", "Enter assessment and plan for hyponatremia, with any medication changes...", key="hyponat_ap_fu")
        prompt = f"""
Visit Date: {visit_date}
Reason for Visit: {reason_for_visit}
[Hyponatremia Follow-Up]

Interval History:
{interval_history}

Labs:
{labs}

Assessment & Plan (with integrated Medication Changes):
{assessment_plan}

Generate a note focused on the follow-up evaluation of hyponatremia.
"""
        generate_note_with_guidelines(prompt, "hyponat_generate_fu", "Hyponatremia")

# --------------------------
# Tab 6: Hypokalemia
# --------------------------
with tabs[5]:
    st.header("Hypokalemia")
    reason_for_visit = st.text_input("Reason for Visit", "Hypokalemia Evaluation/Follow-Up", key="hypokalemia_reason")
    if visit_type == "New Patient":
        hpi = st.text_area("HPI", "Enter patient's HPI (symptoms such as muscle weakness, cramps, etc.)", key="hypokalemia_hpi")
        labs = st.text_area("Labs", "Enter lab data (serum potassium, magnesium, ECG, etc.)", key="hypokalemia_labs_new")
        assessment_plan = st.text_area("Assessment & Plan", "Enter assessment and plan for hypokalemia...", key="hypokalemia_ap_new")
        prompt = f"""
Visit Date: {visit_date}
Reason for Visit: {reason_for_visit}
[Hypokalemia New Patient Evaluation]

HPI:
{hpi}

Labs:
{labs}

Assessment & Plan:
{assessment_plan}

Generate a note focused on the evaluation of hypokalemia for a new patient visit.
"""
        generate_note_with_guidelines(prompt, "hypokalemia_generate_new", "Hypokalemia")
    else:
        interval_history = st.text_area("Interval History", "Enter interval history (changes since last visit)...", key="hypokalemia_interval")
        labs = st.text_area("Labs", "Enter updated lab data...", key="hypokalemia_labs_fu")
        assessment_plan = st.text_area("Assessment & Plan (include Medication Changes)", "Enter assessment and plan for hypokalemia, with any medication changes...", key="hypokalemia_ap_fu")
        prompt = f"""
Visit Date: {visit_date}
Reason for Visit: {reason_for_visit}
[Hypokalemia Follow-Up]

Interval History:
{interval_history}

Labs:
{labs}

Assessment & Plan (with integrated Medication Changes):
{assessment_plan}

Generate a note focused on the follow-up evaluation of hypokalemia.
"""
        generate_note_with_guidelines(prompt, "hypokalemia_generate_fu", "Hypokalemia")

# --------------------------
# Tab 7: Proteinuria & Hematuria
# --------------------------
with tabs[6]:
    st.header("Proteinuria & Hematuria")
    reason_for_visit = st.text_input("Reason for Visit", "Proteinuria & Hematuria Evaluation/Follow-Up", key="prot_hema_reason")
    if visit_type == "New Patient":
        hpi = st.text_area("HPI", "Enter patient's HPI (symptoms, onset, etc.)", key="prot_hema_hpi")
        labs = st.text_area("Labs", "Enter lab data (urinalysis, protein quantification, etc.)", key="prot_hema_labs_new")
        assessment_plan = st.text_area("Assessment & Plan", "Enter assessment and plan for proteinuria/hematuria...", key="prot_hema_ap_new")
        prompt = f"""
Visit Date: {visit_date}
Reason for Visit: {reason_for_visit}
[Proteinuria & Hematuria New Patient Evaluation]

HPI:
{hpi}

Labs:
{labs}

Assessment & Plan:
{assessment_plan}

Generate a note focused on the evaluation of proteinuria and hematuria for a new patient visit.
"""
        generate_note_with_guidelines(prompt, "prot_hema_generate_new", "Proteinuria Hematuria")
    else:
        interval_history = st.text_area("Interval History", "Enter interval history (changes since last visit)...", key="prot_hema_interval")
        labs = st.text_area("Labs", "Enter updated lab data...", key="prot_hema_labs_fu")
        assessment_plan = st.text_area("Assessment & Plan (include Medication Changes)", "Enter assessment and plan for proteinuria/hematuria, with any medication changes...", key="prot_hema_ap_fu")
        prompt = f"""
Visit Date: {visit_date}
Reason for Visit: {reason_for_visit}
[Proteinuria & Hematuria Follow-Up]

Interval History:
{interval_history}

Labs:
{labs}

Assessment & Plan (with integrated Medication Changes):
{assessment_plan}

Generate a note focused on the follow-up evaluation of proteinuria and hematuria.
"""
        generate_note_with_guidelines(prompt, "prot_hema_generate_fu", "Proteinuria Hematuria")

# --------------------------
# Tab 8: Renal Cyst
# --------------------------
with tabs[7]:
    st.header("Renal Cyst")
    reason_for_visit = st.text_input("Reason for Visit", "Renal Cyst Evaluation/Follow-Up", key="renal_cyst_reason")
    if visit_type == "New Patient":
        hpi = st.text_area("HPI", "Enter patient's HPI (if symptomatic, or note if incidental)...", key="renal_cyst_hpi")
        imaging = st.text_area("Imaging Findings", "Enter details from imaging (size, location, complexity)...", key="renal_cyst_imaging_new")
        labs = st.text_area("Labs", "Enter lab data (if available)...", key="renal_cyst_labs_new")
        assessment_plan = st.text_area("Assessment & Plan", "Enter assessment and plan for renal cyst...", key="renal_cyst_ap_new")
        prompt = f"""
Visit Date: {visit_date}
Reason for Visit: {reason_for_visit}
[Renal Cyst New Patient Evaluation]

HPI:
{hpi}

Imaging Findings:
{imaging}

Labs:
{labs}

Assessment & Plan:
{assessment_plan}

Generate a note focused on the evaluation of a renal cyst for a new patient visit.
"""
        generate_note_with_guidelines(prompt, "renal_cyst_generate_new", "Renal Cyst")
    else:
        interval_history = st.text_area("Interval History", "Enter interval history (changes since last visit)...", key="renal_cyst_interval")
        imaging = st.text_area("Imaging Findings", "Enter updated imaging details (if any)...", key="renal_cyst_imaging_fu")
        labs = st.text_area("Labs", "Enter updated lab data...", key="renal_cyst_labs_fu")
        assessment_plan = st.text_area("Assessment & Plan (include Medication Changes)", "Enter assessment and plan for renal cyst, with any medication changes...", key="renal_cyst_ap_fu")
        prompt = f"""
Visit Date: {visit_date}
Reason for Visit: {reason_for_visit}
[Renal Cyst Follow-Up]

Interval History:
{interval_history}

Imaging Findings:
{imaging}

Labs:
{labs}

Assessment & Plan (with integrated Medication Changes):
{assessment_plan}

Generate a note focused on the follow-up evaluation of a renal cyst.
"""
        generate_note_with_guidelines(prompt, "renal_cyst_generate_fu", "Renal Cyst")
