import streamlit as st
import openai
import json

# Secure your API key in .streamlit/secrets.toml:
# OPENAI_API_KEY = "your_api_key_here"

# Configure OpenAI API
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Define canonical triggers (names only)
TRIGGERS = {
    "AKI": "",
    "AKI on CKD": "",
    "AKI workup": "",
    "AKI management": "",
    "Proteinuria workup": "",
    "Hypercalcemia workup": "",
    "Hypercalcemia management": "",
    "Hyperkalemia management": "",
    "Acid-base disturbance": "",
    "Hyponatremia workup": "",
    "Hyponatremia management": "",
    "CRRT initiation": "",
    "ESRD management": "",
    "Peritoneal dialysis prescription": "",
    "Dialysis modality discussion": "",
    "Anemia management": "",
    "Bone mineral disorder management": "",
    "CRS management": "",
    "Hemodialysis initiation": ""
}

# Extractor: lists which triggers to include
EXTRACTOR_SYSTEM = f"""
You are a trigger-extraction assistant. Given a free-form user request, return a JSON array of exact trigger names chosen from this list:
{json.dumps(list(TRIGGERS.keys()))}
Only output the JSON array.
"""

# Generator: dynamic, paragraph-style rationale and plan
GENERATOR_SYSTEM = """
You are a board-certified nephrology consultant. Produce a note with the following sections:

**Reason for Consultation**  
<one-line reason>

**HPI**  
<verbatim HPI as entered by the user>

**Assessment & Plan**
For each triggered problem, write a concise paragraph that:
- Begins with the problem name (e.g., “AKI:”),
- Explains the clinical reasoning using details from the HPI, Labs, and user’s requested details,
- Outlines both workup and management in the same paragraph, using active verbs and clinical shorthand (e.g., “order,” “hold,” “initiate,” “monitor”).

Include the user’s free-text instructions (“Requested Details”) verbatim to guide your reasoning. Avoid bullet headings within each paragraph.
"""

# Streamlit UI
st.title("AI Note Writer for Nephrology Consultations")

reason = st.text_input("Reason for Consultation:")
hpi = st.text_area("HPI (2–3 sentences):", height=80)
labs = st.text_area("Labs (e.g., Cr, Na, K, Ca):", height=80)
free_text = st.text_area(
    "Requested Details (Assessment & Plan instructions):", height=100,
    help="E.g., 'AKI: Oligoanuric, suspect contrast nephropathy; order Foley, strict I/O; initiate HD.'"
)

if st.button("Generate Consultation Note"):
    # 1st: Extract triggers from free_text
    resp1 = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": EXTRACTOR_SYSTEM},
            {"role": "user", "content": free_text}
        ],
        temperature=0
    )
    selected = json.loads(resp1.choices[0].message.content)

    # 2nd: Build content for generation
    user_content = (
        f"**Reason for Consultation:** {reason}\n\n"
        f"**HPI:** {hpi}\n\n"
        f"**Labs:** {labs}\n\n"
        f"**Requested Details:** {free_text}\n\n"
        f"**Assessment & Plan:**\n"
        f"Included Problems: {', '.join(selected)}"
    )

    # 3rd: Generate the note
    resp2 = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": GENERATOR_SYSTEM},
            {"role": "user", "content": user_content}
        ],
        max_tokens=1200,
        temperature=0.7
    )
    st.subheader("Consultation Note")
    st.markdown(resp2.choices[0].message.content.strip())

