import streamlit as st
import openai
import json

# Secure your API key in .streamlit/secrets.toml:
# OPENAI_API_KEY = "your_api_key_here"

# Configure OpenAI API
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Define canonical triggers with descriptions
TRIGGERS = {
    "AKI on CKD": "Scan for precipitants; renal ultrasound, urinalysis, quantify proteinuria, urine electrolytes (Na, Cl, Cr), urine eosinophils; optimize volume, hold ACEI/ARB, adjust diuretics, monitor output and creatinine",
    "AKI workup": "Renal ultrasound, urinalysis, quantify proteinuria, urine electrolytes (Na, Cl, Cr), urine eosinophils",
    "AKI management": "Optimize volume status with isotonic fluids, hold ACEI/ARB, adjust diuretics, monitor urine output and creatinine",
    "Proteinuria workup": "Order ANA, ANCA, PLA2R, SPEP, free light chain ratio",
    "Hypercalcemia workup": "Order SPEP, PTH, PTHrP, free light chain ratio, ACE level, vitamin D (calcitriol) level, CXR",
    "Hypercalcemia management": "Administer IV fluids; Pamidronate 90 mg IV once; Calcitriol 4 IU/kg every 12h",
    "Hyperkalemia management": "Administer IV calcium gluconate 2 g; regular insulin 10 U IV with D50 1 amp; Na-bicarbonate 50 mEq IV once; start Lokelma 10 g TID",
    "Acid-base disturbance": "Perform ABG, calculate anion gap, check lactate and electrolytes, assess RTA",
    "Hyponatremia workup": "Urine sodium, urine osmolality, uric acid, serum osmolality, cortisol, TSH",
    "Hyponatremia management": "Serial sodium monitoring; target sodium correction 6-8 mEq/L in 24 hours",
    "CRRT initiation": "CVVHDF @25 cc/kg/hr; UF 0-100 cc/hr as tolerated; serial BMP q8h; daily phosphorus; dose meds to eGFR 25-30 mL/min; discuss risks/benefits with family",
    "ESRD management": "Dialysis schedule MWF or TTS; access type (tunneled catheter vs AV fistula); outpatient HD unit",
    "Peritoneal dialysis prescription": "Home PD prescription: number of exchanges, fill volume, dwell time, bag type as per patient's regimen",
    "Dialysis modality discussion": "Discuss in-center vs home vs conservative dialysis; address patient concerns and questions during this visit",
    "Anemia management": "Check iron panel if not provided; administer ESA weekly (CKD) or on HD days (ESRD); transfuse if hemoglobin <7 g/dL",
    "Bone mineral disorder management": "Order serum phosphorus and PTH if missing; start phosphate binders; consider vitamin D analog therapy",
    "CRS management": "Scan echocardiogram for EF and diastolic dysfunction; review diuretic dosing and weight trends; optimize diuretics and fluid management; note inability to initiate ACEi/ARB/ARNI/MRA/SGLT-2 inhibitors if AKI present",
    "Hemodialysis initiation": "Initiate intermittent HD for acute indications (oliguria, refractory hyperkalemia, severe metabolic acidosis, refractory volume overload, uremia); discuss risks/complications; define prescription and coordinate with HD unit"
}

# System prompt for trigger extraction
EXTRACTOR_SYSTEM = f"""
You are a trigger-extraction assistant. Given a free-form user request, return a JSON array of exact trigger names chosen from this list:
{json.dumps(list(TRIGGERS.keys()))}
Only output the JSON array.
"""

# System prompt for note formatting and expansion
GENERATOR_SYSTEM = """
You are a board-certified nephrology AI assistant. Always output notes formatted exactly as below, in this order:

**Reason for Consultation**  
<one-line reason>

**HPI**  
2–3 concise sentences summarizing age, timeline, key events, and labs (include all labs provided).

**Assessment & Plan**  
For each trigger:
1. **<Problem Name>**: One-line explanation with supporting data.
   - <Action bullet or single-line order>
"""

# Streamlit UI
st.title("AI Note Writer for Nephrology Consultations")

reason = st.text_input("Reason for Consultation:")
hpi = st.text_area("HPI (2–3 sentences):", height=80)
labs = st.text_area("Labs (e.g., Cr, Na, K, Ca):", height=80)
free_text = st.text_area(
    "Assessment & Plan (free text):", height=100,
    help="E.g., 'Include AKI workup, start Bumex, hyponatremia management'"
)

if st.button("Generate Consultation Note"):
    # 1st: Extract triggers
    resp1 = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": EXTRACTOR_SYSTEM},
            {"role": "user", "content": free_text}
        ],
        temperature=0
    )
    selected = json.loads(resp1.choices[0].message.content)

    # Build combined A&P
    ap_shorthand = "\n".join(f"{t}: {TRIGGERS[t]}" for t in selected)

    # 2nd: Generate note
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

