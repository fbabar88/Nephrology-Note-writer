import streamlit as st
import openai
import json

# Secure your API key in .streamlit/secrets.toml:
# OPENAI_API_KEY = "your_api_key_here"

# Configure OpenAI API
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Define your trigger descriptions
TRIGGERS = {
    "AKI workup": "Renal ultrasound, urine electrolytes (Na, Cl, Cr), quantify proteinuria",
    "AIN workup": "Urine eosinophils",
    "Proteinuria workup": "ANA, ANCA, SPEP, free light chain ratio, PLA2R",
    "Screen for monoclonal gammopathy": "SPEP, free light chain ratio",
    "Evaluate for infection-related GN": "C3, C4, quantify proteinuria, AIN workup (urine eosinophils)",
    "Post renal AKI": "Bladder scan",
    "Anemia of chronic disease workup": "Iron saturation, ferritin, transferrin saturation",
    "Hypercalcemia workup": "PTH, vitamin D, calcitriol, SPEP, free light chain ratio, PTHrP, ACE level",
    "Bone mineral disease": "Phosphorus, PTH",
    "Hyponatremia workup": "Urine sodium, urine osmolality, TSH, cortisol (skip if already ordered)",
    "HRS workup": "Urine sodium and creatinine to calculate FeNa",
    "Start isotonic bicarbonate fluid": "D5W + 150 mEq sodium bicarbonate",
    "Low chloride fluid": "Lactated Ringer's",
    "Lokelma": "10 g daily",
    "Start Bumex": "2 mg IV twice daily",
    "Hyponatremia": "Target sodium correction 6–8 mEq/L, D5W ± DDAVP if rapid correction, serial sodium monitoring",
    "Samsca protocol": "Tolvaptan 7.5 mg daily, serial sodium monitoring, liberalize water intake, monitor neurological status",
    "Initiate CRRT": "CVVHDF @ 25 cc/kg/hr, UF 0–100 cc/hr, BMP q8h, daily phosphorus, dose meds to eGFR 25 mL/min",
    "Start HD": "Discuss side effects: hypotension, cramps, chills, arrhythmias, death",
    "Septic shock": "On antibiotics, pressor support",
    "Hypoxic respiratory failure": "Intubated on mechanical ventilation",
    "HRS management": "Albumin 25% 1 g/kg/day ×48 h, Midodrine 10 mg TID, Octreotide 100 mcg BID, target SBP ≥ 110 mmHg"
}

# Define function schemas
extract_fn = {
    "name": "extract_triggers",
    "description": "Given free text, return an array of trigger names exactly matching the master list",
    "parameters": {
        "type": "object",
        "properties": {
            "triggers": {
                "type": "array",
                "items": {"type": "string", "enum": list(TRIGGERS.keys())}
            }
        },
        "required": ["triggers"]
    }
}

generate_fn = {
    "name": "generate_note",
    "description": "Generate a full nephrology consult note given reason, HPI, labs, and exact triggers",
    "parameters": {
        "type": "object",
        "properties": {
            "note": {"type": "string"}
        },
        "required": ["note"]
    }
}

# Compose system prompt
FULL_SYSTEM = f"""
You are a board-certified nephrology AI assistant.
When given a user message, you should:

1) Call the function `extract_triggers` to pick out any of these exact triggers:
{list(TRIGGERS.keys())}

2) Then call the function `generate_note` with a single string argument "note" containing the final consultation note, formatted exactly as:

**Reason for Consultation**
<one-line reason>

**HPI**
2–3 concise sentences summarizing age, timeline, key events, and labs.

**Assessment & Plan**
For each trigger:
1. **<Trigger Name>**: One-line explanation with supporting lab data.
   - <order from TRIGGERS>
"""

# Streamlit UI
st.title("AI Note Writer for Nephrology Consultations")

reason = st.text_input("Reason for Consultation:")
hpi = st.text_area("HPI (2–3 sentences):", height=80)
labs = st.text_area("Labs (e.g., Cr, Na, Ca):", height=80)
free_text = st.text_area(
    "Assessment & Plan (free text):", height=100,
    help="E.g., 'Please include AKI workup, start Bumex, hyponatremia workup'"
)

if st.button("Generate Consultation Note"):
    user_raw = (
        f"Reason: {reason}\n"
        f"HPI: {hpi}\n"
        f"Labs: {labs}\n"
        f"Assessment & Plan notes: {free_text}"
    )
    with st.spinner("Generating note..."):
        resp = openai.ChatCompletion.create(
            model="gpt-4-0613",
            messages=[
                {"role": "system", "content": FULL_SYSTEM},
                {"role": "user", "content": user_raw}
            ],
            functions=[extract_fn, generate_fn],
            function_call="auto"
        )
    msg = resp.choices[0].message
    if msg.get("function_call") and msg.function_call.name == "generate_note":
        note = json.loads(msg.function_call.arguments)["note"]
    else:
        note = "⚠️ Error: No note returned."
    st.subheader("Consultation Note")
    st.markdown(note)
