import streamlit as st
import openai
import json
import datetime

# Secure your API key in .streamlit/secrets.toml:
# OPENAI_API_KEY = "your_api_key_here"

# Configure OpenAI API
openai.api_key = st.secrets["OPENAI_API_KEY"]

# System prompt for consultation note formatting and expansion
SYSTEM_PROMPT = """
You are a board-certified nephrology AI assistant. Always output notes formatted exactly as below:

**Reason for Consultation**  
<one-line reason>

**HPI**  
2–3 concise sentences summarizing age, timeline, key events, and labs.

**Assessment & Plan**  
For each shorthand line, expand into:
1. **<Problem Name>**: One-line explanation with data.
   - <Action 1>
   - <Action 2>
   - …
"""

# Initialize session state
if 'current_note' not in st.session_state:
    st.session_state.current_note = ""

st.title("AI Note Writer for Nephrology Consultations")

# Section 1: Generate Consultation Note
st.header("1. Generate Consultation Note")
reason = st.text_input("Reason for Consultation:")
hpi = st.text_area("HPI (2–3 sentences):", height=80)
labs = st.text_area("Labs (e.g., Cr, calcium):", height=80)
ap_shorthand = st.text_area(
    "Assessment & Plan (shorthand):",
    "AKI: Hemodynamic injury, contrast exposure on admission 4/22\n"
    "Hypercalcemia: Total Ca ~13, one pamidronate dose\n"
    "Metastatic disease: Unknown primary, liver/spleen lesions\n"
    "Hypovolemia\n"
    "Metabolic acidosis: Due to AKI"
)

if st.button("Generate Consultation Note"):
    user_input = (
        f"**Reason for Consultation:** {reason}\n\n"
        f"**HPI:** {hpi}\n\n"
        f"**Labs:** {labs}\n\n"
        f"**Assessment & Plan:**\n{ap_shorthand}"
    )
    with st.spinner("Generating Note..."):
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ],
            max_tokens=1200,
            temperature=0.7,
        )
    st.session_state.current_note = response.choices[0].message.content.strip()

# Display generated note
if st.session_state.current_note:
    st.subheader("Consultation Note")
    st.markdown(st.session_state.current_note)

# (Optional) Dataset collection and additional sections can follow unchanged.
