import streamlit as st
import openai
import json

# Secure your API key in .streamlit/secrets.toml:
# OPENAI_API_KEY = "your_api_key_here"

# Configure OpenAI API
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Define trigger descriptions
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

# Extraction system prompt
EXTRACTOR_SYSTEM = f"""
You are a trigger-extraction assistant. Given a free-form user message, return a JSON list of exact trigger names chosen from this master list:
{json.dumps(list(TRIGGERS.keys()))}
Only output the JSON array.
"""

# Generation system prompt
GENERATOR_SYSTEM = """
You are a board-certified nephrology AI assistant. Always output notes formatted exactly as below, in this order:

**Reason for Consultation**  
<one-line reason>

**HPI**  
2–3 concise sentences summarizing age, timeline, key events, and labs.

**Assessment & Plan**  
For each trigger, expand into:
1. **<Problem Name>**: One-line explanation with supporting data (include relevant lab values).
   - <Action bullet or single-line order, per trigger definition>

Include each trigger’s diagnostic or therapeutic instructions exactly as defined.
"""

# Define function schema for extraction only
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

# Streamlit UI
st.title("AI Note Writer for Nephrology Consultations")

reason = st.text_input("Reason for Consultation:")
hpi = st.text_area("HPI (2–3 sentences):", height=80)
labs = st.text_area("Labs (e.g., Cr, Na, Ca):", height=80)
free_text = st.text_area(
    "Assessment & Plan (free text):", height=120,
    help="List or describe the triggers you want, e.g. 'AKI workup, Start HD, Lokelma'"
)

if st.button("Generate Consultation Note"):
    # Extract triggers
    with st.spinner("Extracting triggers..."):
        resp1 = openai.ChatCompletion.create(
            model="gpt-4-0613",
            messages=[
                {"role": "system", "content": EXTRACTOR_SYSTEM},
                {"role": "user", "content": free_text}
            ],
            functions=[extract_fn],
            function_call={"name": "extract_triggers"},
            temperature=0
        )
        triggers = json.loads(resp1.choices[0].message.function_call.arguments)["triggers"]

    # Prepare shorthand based on extracted triggers
    ap_shorthand = "\n".join(f"{t}: {TRIGGERS[t]}" for t in triggers)

    # Build the content for generation
    user_content = (
        f"**Reason for Consultation:** {reason}\n\n"
        f"**HPI:** {hpi}\n\n"
        f"**Labs:** {labs}\n\n"
        f"**Assessment & Plan:**\n{ap_shorthand}"
    )

    # Generate final note
    with st.spinner("Generating note..."):
        resp2 = openai.ChatCompletion.create(
            model="gpt-4-0613",
            messages=[
                {"role": "system", "content": GENERATOR_SYSTEM},
                {"role": "user", "content": user_content}
            ],
            temperature=0.7,
            max_tokens=1200
        )
        note = resp2.choices[0].message.content.strip()

    st.subheader("Consultation Note")
    st.markdown(note)
