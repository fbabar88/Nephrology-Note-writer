import streamlit as st
import openai
import json

# Secure your API key in .streamlit/secrets.toml:
# OPENAI_API_KEY = "your_api_key_here"

# Configure OpenAI API\openai.api_key = st.secrets["OPENAI_API_KEY"]

# Define trigger descriptions\TRIGGERS = {
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

# Function schemas
extract_fn = {
    "name": "extract_triggers",
    "description": "Extract nephrology triggers from free text",
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
    "description": "Generate a full nephrology consultation note",
    "parameters": {
        "type": "object",
        "properties": {
            "note": {"type": "string"}
        },
        "required": ["note"]
    }
}

# System prompt for both extraction and generation
FULL_SYSTEM = f"""
You are a board-certified nephrology AI assistant.

Step 1: Extract any of these exact triggers by calling `extract_triggers`:
{list(TRIGGERS.keys())}

Step 2: Using those triggers, generate the final note by calling `generate_note`.
The note must be formatted EXACTLY as below:

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
    "Assessment & Plan details (free text):", height=100,
    help="E.g., 'Rise in Cr due to contrast nephropathy; start workup and diuresis'"
)

if st.button("Generate Consultation Note"):
    user_raw = (
        f"Reason: {reason}\n"
        f"HPI: {hpi}\n"
        f"Labs: {labs}\n"
        f"Notes: {free_text}"
    )
    with st.spinner("Extracting triggers..."):
        # 1) Call extract_triggers
        resp1 = openai.ChatCompletion.create(
            model="gpt-4-0613",
            messages=[
                {"role": "system", "content": FULL_SYSTEM},
                {"role": "user", "content": user_raw}
            ],
            functions=[extract_fn],
            function_call={"name": "extract_triggers"}
        )
        triggers = json.loads(resp1.choices[0].message.function_call.arguments)["triggers"]

    with st.spinner("Generating note..."):
        # 2) Provide function response and call generate_note
        messages = [
            {"role": "system", "content": FULL_SYSTEM},
            {"role": "user", "content": user_raw},
            {"role": "function", "name": "extract_triggers", "content": json.dumps({"triggers": triggers})}
        ]
        resp2 = openai.ChatCompletion.create(
            model="gpt-4-0613",
            messages=messages,
            functions=[generate_fn],
            function_call={"name": "generate_note"}
        )
        note = json.loads(resp2.choices[0].message.function_call.arguments)["note"]

    st.subheader("Consultation Note")
    st.markdown(note)
