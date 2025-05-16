import streamlit as st
import openai
import json

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
    "Hyponatremia": "Target sodium correction 6-8 mEq/L, D5W ± DDAVP if rapid correction, serial sodium monitoring",
    "Samsca protocol": "Tolvaptan 7.5 mg daily, serial sodium monitoring, liberalize water intake, monitor neurological status",
    "Initiate CRRT": "CVVHDF @ 25 cc/kg/hr, UF 0-100 cc/hr, BMP q8h, daily phosphorus, dose meds to eGFR 25 mL/min",
    "Start HD": "Discuss side effects: hypotension, cramps, chills, arrhythmias, death",
    "Septic shock": "On antibiotics, pressor support",
    "Hypoxic respiratory failure": "Intubated on mechanical ventilation",
    "HRS management": "Albumin 25% 1 g/kg/day x48 h, Midodrine 10 mg TID, Octreotide 100 mcg BID, target SBP >= 110 mmHg"
}

# Enhanced extraction prompt for trigger names
EXTRACTOR_SYSTEM = f"""
You are a trigger-extraction assistant. Given a free-form user message:
1. Return a JSON object containing:
   - "triggers": array of exact trigger names from this master list: {json.dumps(list(TRIGGERS.keys()))}
   - "free_text_items": array of additional assessment/plan items not covered by triggers
2. Ensure no information is lost between triggers and free text items.

Example output:
{{
    "triggers": ["AKI workup", "Bone mineral disease"],
    "free_text_items": ["Continue current immunosuppression regimen", "Follow up in transplant clinic in 1 week"]
}}
"""

# Enhanced generation prompt for the full note
GENERATOR_SYSTEM = """
You are a board-certified nephrology AI assistant. Compose a complete consultation note using the sections below, in this exact order:

**Reason for Consultation**
Use the reason text provided as a single line.

**HPI**
Provide 2-3 concise sentences summarizing the patient's age, timeline, key events, and lab trends.

**Labs**
List the key lab values as provided, e.g.: "Cr 5.4 mg/dL; K 7.4 mEq/L; HCO3 9 mEq/L."

**Assessment & Plan**
1. First, address all trigger-based items with clear, actionable plans.
2. Then, incorporate any additional assessment/plan items from the free text.
3. Ensure a cohesive narrative that integrates both structured triggers and free-text information.
4. Use direct imperative phrasing for all recommendations.
5. Acknowledge completed tests and incorporate relevant context.
6. Maintain logical flow between related items.

Example:
1. **AKI workup**: Non-oliguric acute kidney injury, Cr rose from 0.8 to 5.4 mg/dL. Renal ultrasound completed showing normal kidneys. Order urine electrolytes (Na, Cl, Cr) and quantify proteinuria.
2. **Additional Management**: Continue current immunosuppression regimen as previously adjusted. Schedule follow-up in transplant clinic in 1 week for close monitoring.
"""

# Define enhanced extraction function schema
extract_fn = {
    "name": "extract_content",
    "description": "Extract nephrology triggers and additional items from free text",
    "parameters": {
        "type": "object",
        "properties": {
            "triggers": {
                "type": "array",
                "items": {"type": "string", "enum": list(TRIGGERS.keys())}
            },
            "free_text_items": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["triggers", "free_text_items"]
    }
}

# Streamlit UI
st.title("AI Note Writer for Nephrology Consultations")

reason = st.text_input("Reason for Consultation:")
hpi = st.text_area("HPI (2-3 sentences):", height=80)
labs = st.text_area("Labs (e.g., Cr, Na, Ca):", height=80)
free_text = st.text_area(
    "Additional Context / A&P notes:", height=120,
    help="Include any additional assessment and plan items, completed tests, or specific context."
)

if st.button("Generate Consultation Note"):
    # 1) Extract triggers and free text items
    with st.spinner("Processing input..."):
        resp1 = openai.ChatCompletion.create(
            model="gpt-4-0613",
            messages=[
                {"role": "system", "content": EXTRACTOR_SYSTEM},
                {"role": "user", "content": free_text}
            ],
            functions=[extract_fn],
            function_call={"name": "extract_content"},
            temperature=0
        )
        content = json.loads(resp1.choices[0].message.function_call.arguments)
        triggers = content["triggers"]
        free_text_items = content["free_text_items"]

    # 2) Validate content
    if not triggers and not free_text_items:
        st.error("No valid assessment and plan items found. Please check your input.")
    else:
        # 3) Build enhanced user_content for generation
        trigger_content = "\n".join(f"TRIGGER: {t}: {TRIGGERS[t]}" for t in triggers)
        free_text_content = "\n".join(f"FREE TEXT: {item}" for item in free_text_items)
        
        user_content = (
            f"**Reason for Consultation:** {reason}\n\n"
            f"**HPI:** {hpi}\n\n"
            f"**Labs:** {labs}\n\n"
            f"**Assessment & Plan Items:**\n{trigger_content}\n{free_text_content}\n\n"
            f"**Original Context:** {free_text}"
        )

        # 4) Generate final note
        with st.spinner("Generating comprehensive note..."):
            resp2 = openai.ChatCompletion.create(
                model="gpt-4-0613",
                messages=[
                    {"role": "system", "content": GENERATOR_SYSTEM},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            note = resp2.choices[0].message.content.strip()

        st.subheader("Consultation Note")
        st.markdown(note)
