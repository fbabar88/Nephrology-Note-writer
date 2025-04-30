import streamlit as st
import openai
import json
import datetime

# Secure your API key in .streamlit/secrets.toml:
# OPENAI_API_KEY = "your_api_key_here"

# Configure OpenAI API
openai.api_key = st.secrets["OPENAI_API_KEY"]

# System prompt for note formatting, lab integration, diagnostic & therapeutic triggers
SYSTEM_PROMPT = """
You are a board-certified nephrology AI assistant. Always output notes formatted exactly as below, in this order:

**Reason for Consultation**  
<one-line reason>

**HPI**  
2–3 concise sentences summarizing age, timeline, key events, and labs (include all labs provided).

**Assessment & Plan**  
For each shorthand line, expand into:
1. **<Problem Name>**: One-line explanation with supporting data (include relevant lab values).
   - <Action>
   - …

**Important**:
- Always include **Reason for Consultation** and **HPI** sections at the top.
- Do not start plan bullets with “The patient”; begin with the action verb or order.

**Diagnostic Workup Triggers**  
- AKI workup: Renal ultrasound, urine electrolytes (Na, Cl, Cr), quantify proteinuria.
- AIN workup: Urine eosinophils.
- Proteinuria workup: ANA, ANCA, SPEP, free light chain ratio, PLA2R.
- Screen for monoclonal gammopathy: SPEP, free light chain ratio.
- Evaluate for infection-related GN: C3, C4, quantify proteinuria, AIN workup (urine eosinophils).
- Post renal AKI: Bladder scan.
- Anemia of chronic disease workup: Iron saturation, ferritin, transferrin saturation.
- Hypercalcemia workup: PTH, vitamin D, calcitriol, SPEP, free light chain ratio, PTHrP, ACE level.
- Bone mineral disease: Phosphorus, PTH.
- Hyponatremia workup: Urine sodium, urine osmolality, TSH, cortisol (skip if already ordered).
- HRS workup: Urine sodium and creatinine to calculate FeNa.

**Therapeutic Triggers**  
- Start isotonic bicarbonate fluid: D5W + 150 mEq sodium bicarbonate.
- Low chloride fluid: Lactated Ringer's.
- Lokelma: 10 g daily.
- Start Bumex: 2 mg IV twice daily.
- Hyponatremia: Target sodium correction 6–8 mEq/L, include D5W +/- DDAVP if rapid correction, serial sodium monitoring.
- Samsca protocol: Tolvaptan 7.5 mg daily, serial sodium monitoring, liberalize water intake for 24 hours, monitor neurological status closely.
- Initiate CRRT: CVVHDF @ 25 cc/kg/hr, ultrafiltration 0–100 cc/hr, check BMP every 8 hours, daily phosphorus, dose medications to eGFR 25 mL/min.
- Start HD: Discuss side effects including but not limited to hypotension, cramps, chills, arrhythmias, and death.
- Septic shock: On antibiotics, pressor support.
- Hypoxic respiratory failure: Intubated on mechanical ventilation.
- HRS management: Albumin 25% 1 g/kg/day for 48 hours, Midodrine 10 mg TID, Octreotide 100 mcg BID, target SBP ≥ 110 mmHg.

Ensure triggered items appear in a single line under the appropriate problem heading, following the exact headings and bullet structure.
"""

# Initialize session state
if 'current_note' not in st.session_state:
    st.session_state.current_note = ""

st.title("AI Note Writer for Nephrology Consultations")

# Section 1: Generate Consultation Note
st.header("1. Generate Consultation Note")

reason = st.text_input("Reason for Consultation:")
hpi = st.text_area("HPI (2–3 sentences):", height=80)
labs = st.text_area("Labs (e.g., Cr, sodium, calcium):", height=80)
ap_shorthand = st.text_area(
    "Assessment & Plan (shorthand):",
    "AKI workup\n"
    "Hypercalcemia workup\n"
    "Proteinuria workup\n"
    "Screen for monoclonal gammopathy\n"
    "Evaluate for infection-related GN workup\n"
    "Post renal AKI\n"
    "Anemia of chronic disease workup\n"
    "Bone mineral disease\n"
    "Hyponatremia workup\n"
    "HRS workup\n"
    "Start isotonic bicarbonate fluid\n"
    "Low chloride fluid\n"
    "Lokelma\n"
    "Start Bumex\n"
    "Hyponatremia\n"
    "Samsca protocol\n"
    "Initiate CRRT\n"
    "Start HD\n"
    "Septic shock\n"
    "Hypoxic respiratory failure\n"
    "HRS management"
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
