import streamlit as st
import openai
import datetime
import time

# --------------------------
# Configure the DeepSeek API using the beta endpoint and lower temperature
# --------------------------
openai.api_base = "https://api.deepseek.com/beta"
openai.api_key = st.secrets.get("DEEPSEEK_API_KEY", "YOUR_API_KEY")

# --------------------------
# Final Instruction for Note Generation
# --------------------------
final_instruction = (
    "Generate a comprehensive narrative note in paragraph form, written in the style of a seasoned nephrologist at the end of the visit. "
    "The note should include a clear and succinct Subjective section summarizing the patient's history and current status, and an Assessment & Plan "
    "section formatted as a problem list where each problem is listed along with its corresponding ICD-10 code (if applicable). "
    "Ensure that the final note is evidence-based."
)

st.title("Nephrology Note Generator - Multi-Condition Interface")

# Sidebar: Timer, Visit Type, Condition Selection, and Reset Button
if st.sidebar.button("Start Timer"):
    st.session_state.start_time = time.time()
    st.sidebar.write("Timer started!")

if "start_time" in st.session_state:
    elapsed = time.time() - st.session_state.start_time
    st.sidebar.write(f"Time since start: {elapsed:.2f} seconds")

visit_type = st.sidebar.radio("Select Visit Type", options=["New Patient", "Follow-Up"], key="visit_type")
condition = st.sidebar.selectbox(
    "Select Condition",
    options=["CKD", "Hypertension", "Glomerulonephritis", "Hyponatremia", "Hypokalemia", "Proteinuria & Hematuria", "Renal Cyst"],
    key="condition"
)

if st.sidebar.button("Reset Form"):
    st.session_state.clear()
    st.experimental_rerun()

st.header(f"{condition} Progress Note")

# --------------------------
# Choose between Structured Input and Free Text modes
# --------------------------
input_mode = st.radio("Select Input Mode", options=["Structured Input", "Free Text"], key="input_mode")

if input_mode == "Structured Input":
    if condition == "CKD":
        if visit_type == "New Patient":
            reason_for_visit = st.text_input("Reason for Visit", "CKD Evaluation", key="ckd_new_reason")
            symptoms = st.text_area("Symptoms", "Enter patient's symptoms...", key="ckd_new_symptoms")
            risk_factors = st.text_area("Risk Factors", "Enter risk factors (e.g., NSAIDs, DM, HTN, nephrotoxins)...", key="ckd_new_risk_factors")
            dm_status = st.text_input("Diabetes Mellitus Status", "Present/Absent", key="ckd_new_dm_status")
            htn_status = st.text_input("Hypertension Status", "Present/Absent", key="ckd_new_htn_status")
            labs = st.text_area("Lab Data", "Enter relevant lab data...", key="ckd_new_labs")
            assessment_plan = st.text_area("Assessment & Plan", "Enter assessment and plan (integrate any medication changes)...", key="ckd_new_ap")
            additional_details = st.text_area("Additional Comments (Optional)", "", key="ckd_new_extra")
            
            prompt = f"""
Visit Date: {datetime.date.today().strftime("%B %d, %Y")}
Reason for Visit: {reason_for_visit}
[New Patient - CKD Evaluation]

Subjective:
Patient presents with the following symptoms: {symptoms}.
Risk Factors: {risk_factors}.
Additional Info: Diabetes Mellitus Status: {dm_status}, Hypertension Status: {htn_status}.
Lab Data: {labs}.
Additional Comments: {additional_details}.

Assessment & Plan:
{assessment_plan}

{final_instruction}
            """
        else:
            reason_for_visit = st.text_input("Reason for Visit", "CKD Follow-Up", key="ckd_fu_reason")
            interval_history = st.text_area("Interval History", "Enter changes since last visit...", key="ckd_fu_interval")
            ckd_stage = st.selectbox("CKD Stage", options=["1", "2", "3", "4", "5"], index=2, key="ckd_fu_stage")
            kidney_trend = st.selectbox("Kidney Function Trend", options=["Improving", "Stable", "Worsening"], key="ckd_fu_trend")
            dm_status = st.text_input("Diabetes Mellitus Status", "Controlled/Uncontrolled", key="ckd_fu_dm_status")
            htn_status = st.text_input("Hypertension Status", "Controlled/Uncontrolled", key="ckd_fu_htn_status")
            labs = st.text_area("Lab Data", "Enter updated lab data...", key="ckd_fu_labs")
            assessment_plan = st.text_area("Assessment & Plan", "Enter assessment and plan (integrate any medication changes)...", key="ckd_fu_ap")
            additional_details = st.text_area("Additional Comments (Optional)", "", key="ckd_fu_extra")
            
            prompt = f"""
Visit Date: {datetime.date.today().strftime("%B %d, %Y")}
Reason for Visit: {reason_for_visit}
[Follow-Up - CKD]

Interval History: {interval_history}
CKD Details: Stage: {ckd_stage}, Kidney Function Trend: {kidney_trend}.
Additional Info: Diabetes Mellitus Status: {dm_status}, Hypertension Status: {htn_status}.
Lab Data: {labs}.
Additional Comments: {additional_details}.

Assessment & Plan:
{assessment_plan}

{final_instruction}
            """
    else:
        if visit_type == "New Patient":
            reason_for_visit = st.text_input("Reason for Visit", f"{condition} Evaluation", key=f"{condition}_new_reason")
            hpi = st.text_area("HPI", "Enter patient's HPI (symptoms, onset, etc.)", key=f"{condition}_new_hpi")
            labs = st.text_area("Labs", "Enter lab data, if any...", key=f"{condition}_new_labs")
            assessment_plan = st.text_area("Assessment & Plan", "Enter assessment and plan (integrate any medication changes)...", key=f"{condition}_new_ap")
            additional_comments = st.text_area("Additional Comments (Optional)", "", key=f"{condition}_new_extra")
            
            prompt = f"""
Visit Date: {datetime.date.today().strftime("%B %d, %Y")}
Reason for Visit: {reason_for_visit}

Subjective:
HPI: {hpi}.
Lab Data: {labs}.
Additional Comments: {additional_comments}.

Assessment & Plan:
{assessment_plan}

{final_instruction}
            """
        else:
            reason_for_visit = st.text_input("Reason for Visit", f"{condition} Follow-Up", key=f"{condition}_fu_reason")
            interval_history = st.text_area("Interval History", "Enter interval history (changes since last visit)...", key=f"{condition}_fu_interval")
            labs = st.text_area("Labs", "Enter updated lab data...", key=f"{condition}_fu_labs")
            assessment_plan = st.text_area("Assessment & Plan", "Enter assessment and plan (integrate any medication changes)...", key=f"{condition}_fu_ap")
            additional_comments = st.text_area("Additional Comments (Optional)", "", key=f"{condition}_fu_extra")
            
            prompt = f"""
Visit Date: {datetime.date.today().strftime("%B %d, %Y")}
Reason for Visit: {reason_for_visit}

Interval History: {interval_history}
Lab Data: {labs}.
Additional Comments: {additional_comments}.

Assessment & Plan:
{assessment_plan}

{final_instruction}
            """
else:
    # Free Text Mode
    free_text_input = st.text_area("Enter your note details in free text", "Type your note here...", key="free_text")
    prompt = f"""
Visit Date: {datetime.date.today().strftime("%B %d, %Y")}

{free_text_input}

{final_instruction}
            """

# Display the constructed prompt for review (for debugging)
st.code(prompt, language="plaintext")

# --------------------------
# Generate Note Button
# --------------------------
if st.button("Generate Progress Note", key="generate_note"):
    if "start_time" not in st.session_state:
        st.error("Please start the timer first from the sidebar!")
    else:
        elapsed = time.time() - st.session_state.start_time
        st.write(f"Time taken to input variables: {elapsed:.2f} seconds")
        with st.spinner("Generating progress note..."):
            try:
                response = openai.Completion.create(
                    model="deepseek-chat",
                    prompt=prompt,
                    max_tokens=600,
                    temperature=0.4,
                )
                generated_note = response.choices[0].text.strip()
                st.subheader("Generated Progress Note")
                final_note = st.text_area("Final Note (Editable)", value=generated_note, height=300, key="final_note")
                st.download_button("Download Note", data=final_note, file_name="progress_note.txt", mime="text/plain")
            except Exception as e:
                st.error(f"API call failed: {e}")
