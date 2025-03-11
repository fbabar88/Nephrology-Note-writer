import streamlit as st
import openai
import datetime
import time

# Configure DeepSeek API using the beta endpoint and a lower temperature
openai.api_base = "https://api.deepseek.com/beta"
openai.api_key = st.secrets.get("DEEPSEEK_API_KEY", "YOUR_API_KEY")

st.title("Nephrology Progress Note Generator")

# Sidebar: Timer functionality
if st.sidebar.button("Start Timer"):
    st.session_state.start_time = time.time()
    st.sidebar.write("Timer started!")

if "start_time" in st.session_state:
    elapsed = time.time() - st.session_state.start_time
    st.sidebar.write(f"Time since start: {elapsed:.2f} seconds")

# Display today's date
visit_date = datetime.date.today().strftime("%B %d, %Y")
st.write(f"**Visit Date:** {visit_date}")

# Provide instructions to guide the physician’s input
instructions = """
**Instructions:**
Please enter a brief summary of the patient's clinical scenario in the box below. Your input should include:
- **Symptoms:** A brief description of the patient's symptoms (e.g., fatigue, edema, shortness of breath).
- **Key Labs:** Relevant lab values (e.g., creatinine, potassium, GFR).
- **Additional Relevant Information:** Any other details you believe are important (e.g., medication changes, interval history).

The AI will use this information to generate a comprehensive narrative progress note in paragraph form. The note will have two main sections:
1. **Subjective:** A detailed summary of the patient's history and current complaints.
2. **Assessment & Plan:** A thorough evaluation of the patient's condition along with a clear management plan.

The final note will be written in the style of a seasoned nephrologist at the end of a visit.
"""

st.markdown(instructions)

# Free text box for entering the clinical summary
clinical_summary = st.text_area(
    "Enter Clinical Summary",
    placeholder="E.g., Patient presents with fatigue, edema, and increased creatinine levels. Labs: creatinine 2.1 mg/dL, potassium 4.8 mEq/L. Patient has been compliant with medications, though blood pressure has risen slightly. Please generate a progress note with Subjective and Assessment & Plan sections.",
    key="clinical_summary"
)

# Button to generate the note
if st.button("Generate Progress Note"):
    elapsed = time.time() - st.session_state.get("start_time", time.time())
    st.write(f"Time taken to input variables: {elapsed:.2f} seconds")
    
    # Construct the prompt using the free text input
    prompt = f"""
Visit Date: {visit_date}

Clinical Summary:
{clinical_summary}

Based on the above clinical summary, generate a comprehensive narrative progress note in paragraph form, written in the style of a seasoned nephrologist at the end of a visit. The note should include two main sections:
1. **Subjective:** A detailed summary of the patient's history and current complaints.
2. **Assessment & Plan:** A thorough evaluation of the patient's condition along with a clear management plan.

Generate the note in a concise, coherent paragraph.
    """
    
    st.code(prompt, language="plaintext")
    
    with st.spinner("Generating progress note..."):
        try:
            response = openai.Completion.create(
                model="deepseek-chat",
                prompt=prompt,
                max_tokens=600,
                temperature=0.5,  # Reduced temperature for more focused output
            )
            generated_note = response.choices[0].text.strip()
            st.subheader("Generated Progress Note")
            # Editable final note field
            final_note = st.text_area("Final Note (Editable)", value=generated_note, height=300, key="final_note")
            # Download button for convenience
            st.download_button("Download Note", data=final_note, file_name="progress_note.txt", mime="text/plain")
        except Exception as e:
            st.error(f"API call failed: {e}")
