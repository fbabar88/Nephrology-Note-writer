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
   - <Action 1>
   - <Action 2>
   - …

**Important**:
- Always include **Reason for Consultation** and **HPI** sections at the top.
- Do not start plan bullets with “The patient”; begin with the action verb or order.

**Diagnostic & Therapeutic Workup Triggers**  
- If a problem mentions "AKI workup": order Renal ultrasound, urine electrolytes (Na, Cl, Cr), and quantify proteinuria.
- If a problem mentions "proteinuria workup": order ANA, ANCA, SPEP, free light chain ratio, and PLA2R.
- If a problem mentions "screen for monoclonal gammopathy": order SPEP and free light chain ratio.
- If a problem mentions "evaluate for infection-related GN": order C3, C4, quantify proteinuria, and AIN workup including urine eosinophils.
- If a problem mentions "post renal AKI": order bladder scan.
- If a problem mentions "anemia of chronic disease workup": check iron profile including iron saturation, ferritin, and transferrin saturation.
- If a problem mentions "hypercalcemia workup": check PTH, vitamin D, calcitriol, SPEP, free light chain ratio, PTHrP, and ACE level.
- If a problem mentions "bone mineral disease": check phosphorus and PTH if provided.
- If a problem mentions "hyponatremia workup": order urine sodium, urine osmolality, TSH, cortisol (skip if already ordered).

**Therapeutic Triggers**  
- If the plan includes "start isotonic bicarbonate fluid": specify D5W + 150 mEq sodium bicarbonate.
- If the plan includes "low chloride fluid": specify Lactated Ringer's.
- If the plan includes "Lokelma": add dose of 10 g daily.
- If the plan includes "start Bumex": specify 2 mg IV twice daily.
- If the plan includes "hyponatremia": add target sodium correction of 6–8 mEq/L; include D5W +/- DDAVP if correction is rapid; include serial sodium monitoring.
- If the plan includes "samsca protocol": prescribe tolvaptan 7.5 mg daily; include serial sodium monitoring; liberalize water intake for 24 hours; monitor neurological status closely.

Ensure that triggered orders or formulations are included under the appropriate problem heading as bullet points. Always follow the exact headings and bullet structure.
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
    "Start isotonic bicarbonate fluid\n"
    "Low chloride fluid\n"
    "Lokelma\n"
    "Start Bumex\n"
    "Hyponatremia\n"
    "Samsca protocol"
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
