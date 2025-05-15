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

# Extraction prompt
EXTRACTOR_SYSTEM = f"""
You are a trigger-extraction assistant. Given a free-form user message, return a JSON list of exact trigger names chosen from this master list:
{json.dumps(list(TRIGGERS.keys()))}
Only output the JSON array.
"""

# Generation prompt
GENERATOR_SYSTEM = """
You are a board-certified nephrology AI assistant. Use the input sections below to craft a single, coherent consult note.

- If any procedure or test is already mentioned as done in the HPI or Additional Context, do NOT recommend ordering it again; instead acknowledge its completion in the narrative.
- Always format the note exactly as:

**Reason for Consultation**  
<one-line reason>

**HPI**  
2–3 concise sentences summarizing age, timeline, key events, labs, and context.

**Assessment & Plan**  
For each trigger provided:
1. **<Trigger Name>**: One-line explanation incorporating any relevant lab values or context.  
   - <use the exact action from TRIGGERS>
"""

# Define extraction function schema
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
    "Additional Context / A&P notes:", height=120,
    help="Include any narrative or context, e.g. 'US shows normal structure, so no repeat imaging.'"
)

if st.button("Generate Consultation Note"):
    # 1) Extract triggers
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

    # Ensure valid triggers
    valid_triggers = [t for t in triggers if t in TRIGGERS]
    if not valid_triggers:
        st.error("No valid triggers found. Please check your context input.")
    else:
        # 2) Build shorthand plus include context in generation input
        ap_shorthand = "\n".join(f"{t}: {TRIGGERS[t]}" for t in valid_triggers)
        user_content = (
            f"**Reason for Consultation:** {reason}\n\n"
            f"**HPI:** {hpi}\n\n"
            f"**Labs:** {labs}\n\n"
            f"**Additional Context:** {free_text}\n\n"
            f"**Assessment & Plan:**\n{ap_shorthand}"
        )

        # 3) Generate final note
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
