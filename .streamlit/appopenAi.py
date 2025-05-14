import streamlit as st
import openai
import json

# Secure your API key in .streamlit/secrets.toml:
# OPENAI_API_KEY = "your_api_key_here"

# Configure OpenAI API
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Define canonical triggers with descriptions (static names only)
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

# Extractor: only lists trigger names
EXTRACTOR_SYSTEM = f"""
You are a trigger-extraction assistant. Given a free-form user request, return a JSON array of exact trigger names chosen from this list:
{json.dumps(list(TRIGGERS.keys()))}
Only output the JSON array.
"""

# Generator: dynamic playbook for each trigger
GENERATOR_SYSTEM = """
You are a board-certified nephrology AI assistant. Always output notes formatted exactly as below, in this order:

**Reason for Consultation**  
<one-line reason>

**HPI**  
<Restate the patient's history exactly as provided in the HPI input, using 2–3 concise sentences. Include all key timeline and clinical details.>

**Assessment & Plan**  
For each trigger in the provided list, follow this structure:

- **<Trigger Name>**  
  • **Rationale:** <One-line explanation integrating specific HPI details and lab values.>  
  • **Workup:** <List any required tests not already documented.>  
  • **Management:** <List interventions with specific dosing or monitoring instructions.>

Ensure that:
1. The **HPI** section is always included verbatim; do not omit or paraphrase it.  
2. Use bullet points under each problem, labeled as **Rationale**, **Workup**, and **Management**.  
3. For **AKI on CKD**, explicitly state it is due to **cardiorenal syndrome**.  
4. For **Hyperkalemia management**, use only **Lokelma 10 g TID**.  
5. For **Acid-base disturbance**, include **monitoring of sodium bicarbonate** therapy.  
6. For **CRS management**, specify **Bumex 2 mg IV BID** as the diuretic regimen.
"""

# Streamlit UI
st.title("AI Note Writer for Nephrology Consultations")

reason = st.text_input("Reason for Consultation:")
hpi = st.text_area("HPI (2–3 sentences):", height=80)
labs = st.text_area("Labs (e.g., Cr, Na, K, Ca):", height=80)
free_text = st.text_area(
    "Assessment & Plan (free text):", height=100,
    help="E.g., 'Include AKI, hyperkalemia management, acid-base disturbance, CRS management'"
)

if st.button("Generate Consultation Note"):
    # 1. Extract triggers
    resp1 = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": EXTRACTOR_SYSTEM},
            {"role": "user", "content": free_text}
        ],
        temperature=0
    )
    selected = json.loads(resp1.choices[0].message.content)

    # 2. Build shorthand (static names only)
    ap_shorthand = "\n".join(f"{t}: {TRIGGERS[t]}" for t in selected)

    # 3. Generate note with dynamic playbook
    user_content = (
        f"**Reason for Consultation:** {reason}\n\n"
        f"**HPI:** {hpi}\n\n"
        f"**Labs:** {labs}\n\n"
        f"**Assessment & Plan:**\n{ap_shorthand}"
    )
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
