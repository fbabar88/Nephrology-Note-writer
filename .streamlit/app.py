import streamlit as st
import openai
import datetime

# --------------------------
# Configure the DeepSeek API
# --------------------------
openai.api_base = "https://api.deepseek.com/beta"  # Using the v1 endpoint
openai.api_key = st.secrets.get("DEEPOSEEK_API_KEY", "YOUR_API_KEY")

# --------------------------
# Title and Sidebar
# --------------------------
st.title("Nephrology Note Generator - Multi-Condition Interface")
visit_type = st.sidebar.selectbox("Select Visit Type", options=["New Patient", "Follow-Up"])

# Get today's date (displayed in all notes)
visit_date = datetime.date.today().strftime("%B %d, %Y")

# --------------------------
# Create Tabs for Different Conditions
# --------------------------
tab_labels = [
    "CKD Evaluation (New Patient)",
    "CKD Follow-Up",
    "HTN",
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
    reason_for_visit = st.text_input("Reason for Visit", "CKD Evaluation")
    symptoms = st.text_area("Symptoms", "Enter patient's symptoms...")
    risk_factors = st.text_area("Risk Factors (e.g., NSAIDs, DM, HTN, other nephrotoxins)", "Enter risk factors...")
    dm_status = st.text_input("Diabetes Mellitus Status", "Present/Absent")
    htn_status = st.text_input("Hypertension Status", "Present/Absent")
    labs = st.text_area("Lab Data", "Enter relevant lab data...")
    assessment_plan = st.text_area("Assessment & Plan", "Enter assessment and plan...")

    if st.button("Generate Note for CKD Evaluation"):
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
    reason_for_visit = st.text_input("Reason for Visit", "CKD Follow-Up")
    symptoms = st.text_area("Symptoms", "Enter current symptoms...")
    ckd_stage = st.selectbox("CKD Stage", options=["1", "2", "3", "4", "5"], index=2)
    kidney_trend = st.selectbox("Kidney Function Trend", options=["Improving", "Stable", "Worsening"])
    dm_status = st.text_input("Diabetes Mellitus Status", "Controlled/Uncontrolled")
    htn_status = st.text_input("Hypertension Status", "Controlled/Uncontrolled")
    labs = st.text_area("Lab Data", "Enter updated lab data...")
    assessment_plan = st.text_area("Assessment & Plan", "Enter assessment and plan...")

    if st.button("Generate Note for CKD Follow-Up"):
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
# Tab 3: Hypertension (HTN)
# --------------------------
with tabs[2]:
    st.header("Hypertension (HTN)")
    reason_for_visit = st.text_input("Reason for Visit", "HTN Evaluation/Follow-Up")
    symptoms = st.text_area("Symptoms", "Enter symptoms such as headaches, dizziness, palpitations...")
    vital_signs = st.text_input("Vital Signs", "e.g., 140/90 mmHg")
    medications = st.text_area("Medications & Compliance", "Enter current antihypertensive medications and adherence info...")
    risk_factors = st.text_area("Risk Factors & History", "Enter relevant risk factors (family history, lifestyle, etc.)")
    labs = st.text_area("Lab Data", "Enter lab data, if any...")
    assessment_plan = st.text_area("Assessment & Plan", "Enter assessment and plan for HTN management...")

    if st.button("Generate Note for HTN"):
        prompt = f"""
Visit Date: {visit_date}
Reason for Visit: {reason_for_visit}
[HTN Evaluation/Follow-Up]

Subjective:
Patient reports the following symptoms: {symptoms}.

Vital Signs:
{vital_signs}

Medications & Compliance:
{medications}

Risk Factors & History:
{risk_factors}

Lab Data:
{labs}

Assessment & Plan:
{assessment_plan}

Generate a SOAP note focused on the evaluation and management of hypertension.
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
# Tab 4: Glomerulonephritis
# --------------------------
with tabs[3]:
    st.header("Glomerulonephritis")
    reason_for_visit = st.text_input("Reason for Visit", "Glomerulonephritis Evaluation/Follow-Up")
    symptoms = st.text_area("Symptoms", "Enter symptoms such as hematuria, edema, fatigue...")
    history = st.text_area("History & Risk Factors", "Enter recent infections, family history, systemic symptoms...")
    labs = st.text_area("Lab Data", "Enter urinalysis results, serum creatinine, complement levels, etc.")
    assessment_plan = st.text_area("Assessment & Plan", "Enter assessment and plan for glomerulonephritis...")

    if st.button("Generate Note for Glomerulonephritis"):
        prompt = f"""
Visit Date: {visit_date}
Reason for Visit: {reason_for_visit}
[Glomerulonephritis Evaluation/Follow-Up]

Subjective:
Patient presents with the following symptoms: {symptoms}.

History & Risk Factors:
{history}

Lab Data:
{labs}

Assessment & Plan:
{assessment_plan}

Generate a SOAP note focused on the evaluation and management of glomerulonephritis.
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
# Tab 5: Hyponatremia
# --------------------------
with tabs[4]:
    st.header("Hyponatremia")
    reason_for_visit = st.text_input("Reason for Visit", "Hyponatremia Evaluation/Follow-Up")
    symptoms = st.text_area("Symptoms", "Enter symptoms such as confusion, headache, nausea...")
    med_history = st.text_area("Medication & History", "Enter medications and history contributing to hyponatremia...")
    labs = st.text_area("Lab Data", "Enter serum sodium, osmolality, etc.")
    assessment_plan = st.text_area("Assessment & Plan", "Enter assessment and plan for managing hyponatremia...")

    if st.button("Generate Note for Hyponatremia"):
        prompt = f"""
Visit Date: {visit_date}
Reason for Visit: {reason_for_visit}
[Hyponatremia Evaluation/Follow-Up]

Subjective:
Patient reports the following symptoms: {symptoms}.

Medication & History:
{med_history}

Lab Data:
{labs}

Assessment & Plan:
{assessment_plan}

Generate a SOAP note focused on the management of hyponatremia.
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
# Tab 6: Hypokalemia
# --------------------------
with tabs[5]:
    st.header("Hypokalemia")
    reason_for_visit = st.text_input("Reason for Visit", "Hypokalemia Evaluation/Follow-Up")
    symptoms = st.text_area("Symptoms", "Enter symptoms such as muscle weakness, cramps, fatigue...")
    med_history = st.text_area("Medication & History", "Enter medications (e.g., diuretics) or history causing hypokalemia...")
    labs = st.text_area("Lab Data", "Enter serum potassium, magnesium levels, ECG changes, etc.")
    assessment_plan = st.text_area("Assessment & Plan", "Enter assessment and plan for hypokalemia management...")

    if st.button("Generate Note for Hypokalemia"):
        prompt = f"""
Visit Date: {visit_date}
Reason for Visit: {reason_for_visit}
[Hypokalemia Evaluation/Follow-Up]

Subjective:
Patient reports the following symptoms: {symptoms}.

Medication & History:
{med_history}

Lab Data:
{labs}

Assessment & Plan:
{assessment_plan}

Generate a SOAP note focused on the management of hypokalemia.
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
# Tab 7: Proteinuria & Hematuria
# --------------------------
with tabs[6]:
    st.header("Proteinuria & Hematuria")
    reason_for_visit = st.text_input("Reason for Visit", "Proteinuria & Hematuria Evaluation/Follow-Up")
    symptoms = st.text_area("Symptoms", "Enter symptoms (e.g., visible hematuria, flank pain) or note if asymptomatic...")
    history = st.text_area("History & Risk Factors", "Enter any history of kidney disease, infections, trauma, etc.")
    labs = st.text_area("Lab Data", "Enter urinalysis details, quantitative proteinuria, etc.")
    assessment_plan = st.text_area("Assessment & Plan", "Enter assessment and plan for proteinuria/hematuria management...")

    if st.button("Generate Note for Proteinuria & Hematuria"):
        prompt = f"""
Visit Date: {visit_date}
Reason for Visit: {reason_for_visit}
[Proteinuria & Hematuria Evaluation/Follow-Up]

Subjective:
Patient presents with the following symptoms: {symptoms}.

History & Risk Factors:
{history}

Lab Data:
{labs}

Assessment & Plan:
{assessment_plan}

Generate a SOAP note focused on the evaluation and management of proteinuria and hematuria.
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
# Tab 8: Renal Cyst
# --------------------------
with tabs[7]:
    st.header("Renal Cyst")
    reason_for_visit = st.text_input("Reason for Visit", "Renal Cyst Evaluation/Follow-Up")
    symptoms = st.text_area("Symptoms", "Enter symptoms (if any, or note if incidental finding)...")
    imaging = st.text_area("Imaging Findings", "Enter details from imaging (size, location, complexity)...")
    labs = st.text_area("Lab Data", "Enter any lab data if available (e.g., renal function tests)...")
    assessment_plan = st.text_area("Assessment & Plan", "Enter assessment and plan for renal cyst management...")

    if st.button("Generate Note for Renal Cyst"):
        prompt = f"""
Visit Date: {visit_date}
Reason for Visit: {reason_for_visit}
[Renal Cyst Evaluation/Follow-Up]

Subjective:
Patient presents with the following: {symptoms}.

Imaging Findings:
{imaging}

Lab Data:
{labs}

Assessment & Plan:
{assessment_plan}

Generate a SOAP note focused on the evaluation and management of a renal cyst.
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
