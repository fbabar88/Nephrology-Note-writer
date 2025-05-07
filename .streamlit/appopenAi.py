import streamlit as st
import openai
import json
import datetime

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
    "Hyponatremia management": "Serial sodium monitoring; target correction 6-8 mEq/L in 24 hours",
    "CRRT initiation": "CVVHDF @25 cc/kg/hr; UF 0-100 cc/hr as tolerated; serial BMP q8h; daily phosphorus; dose meds to eGFR 25-30 mL/min; discuss risks/benefits with family",
    "ESRD management": "Dialysis schedule MWF or TTS; access type (tunneled catheter vs AV fistula); outpatient HD unit",
    "Peritoneal dialysis prescription": "Home PD prescription: number of exchanges, fill volume, dwell time, bag type as per patient's regimen",
    "Dialysis modality discussion": "Discuss in-center vs home vs conservative dialysis; address patient concerns and questions during this visit",
    "Anemia management": "Check iron panel if not provided; administer ESA weekly (CKD) or on HD days (ESRD); transfuse if hemoglobin <7 g/dL",
    "Bone mineral disorder management": "Order serum phosphorus and PTH if missing; start phosphate binders; consider vitamin D analog therapy",
    "Dialysis modality discussion": "Discuss in-center vs home vs conservative dialysis; address patient concerns and questions during this visit",
    "CRS management": "Scan echocardiogram for EF and diastolic dysfunction; review diuretic dosing and weight trends; optimize diuretics and fluid management; note inability to initiate ACEi/ARB/ARNI/MRA/SGLT-2 inhibitors if AKI present",
    "Hemodialysis initiation": "Initiate intermittent hemodialysis for acute indications (oliguria, hyperkalemia, severe metabolic acidosis, refractory volume overload, uremia); discuss risks and complications (hypotension, cramps, arrhythmias); define prescription (blood flow rate, dialysate flow, duration) and coordinate with HD unit"
}

# System prompt for trigger extraction with alias mapping
EXTRACTOR_SYSTEM = f"""
You are a trigger-extraction assistant for nephrology consultations. Map free-text from HPI, Labs, or request to these canonical triggers:
{json.dumps(list(TRIGGERS.keys()))}
Use aliases:
- AKI on CKD: "acute-on-chronic", "AKI on CKD", "SCr jumped", "oliguria"...
- AKI workup: "AKI", "acute kidney injury", "urine output <0.5"...
- AKI management: "fluid resuscitation", "hold ACEI"...
- Proteinuria workup: "proteinuria", "Protein/Cr"...
- Hypercalcemia workup: "hypercalcemia", "Ca > 10.2", "elevated calcium"
- Hypercalcemia management: "IV fluids", "Pamidronate", "calcitriol"
- Hyperkalemia management: "hyperkalemia", "K > 5.5", "elevated potassium"
- Acid-base disturbance: "acidosis", "AG > 12", "lactic"...
- Hyponatremia workup: "hyponatremia", "Na < 135"...
- Hyponatremia management: "correct sodium", "serial sodium"...
- CRRT initiation: "CRRT", "CVVHDF", "continuous dialysis"...
- ESRD management: "ESRD", "maintenance dialysis", "MWF", "TTS", "AV fistula"...
- Peritoneal dialysis prescription: "peritoneal dialysis", "PD prescription", "home PD", "CAPD"
- Dialysis modality discussion: "dialysis options", "in-center dialysis", "home dialysis", "conservative care"
- Anemia management: "anemia", "low hemoglobin", "Hb < 7"...
- Bone mineral disorder management: "hyperphosphatemia", "elevated PTH", "renal osteodystrophy"...
- CRS management: "cardiorenal syndrome", "CRS", "echo EF", "diastolic dysfunction", "diuretics", "weight gain"
- Hemodialysis initiation: "hemodialysis initiation", "initiate HD", "start HD", "intermittent HD"
Only return a JSON array of trigger names.
"""

# System prompt for note generation with context-check and extended logic
GENERATOR_SYSTEM = """
You are a board-certified nephrology AI assistant. Format notes:

**Reason for Consultation**  
<one-line reason>

**HPI**  
2–3 concise sentences summarizing key history, timeline, labs, imaging.

**Assessment & Plan**  
For each trigger:

- **AKI on CKD**:
  • **Rationale**: Scan for precipitants (volume overload, hypovolemia, contrast, meds, urinary retention, hydronephrosis).
  • **Context**: Integrate documented tests.
  • **Plan**: Remaining tests/interventions.

- **AKI workup**:
  • Order renal US, UA, quantify proteinuria, urine electrolytes, urine eosinophils if not done.

- **AKI management**:
  • Optimize volume, hold ACEi/ARB, adjust diuretics, monitor output and creatinine.

- **Proteinuria workup**:
  • Rationale: Scan for diabetes history.
  • Plan: ANA, ANCA, PLA2R, SPEP, free light chain ratio.

- **Hypercalcemia workup**:
  • Rationale: Identify elevated calcium; integrate existing calcium values.
  • Plan: Order SPEP, PTH, PTHrP, free light chain ratio, ACE level, vitamin D (calcitriol) level, CXR.

- **Hypercalcemia management**:
  • Plan: Administer IV fluids; Pamidronate 90 mg IV once; Calcitriol 4 IU/kg every 12h.

- **Hyperkalemia management**:
  • Rationale: Identify elevated potassium and ECG changes.
  • Plan: Administer IV calcium gluconate 2g; insulin 10U IV with D50; Na-bicarb 50 mEq IV; start Lokelma 10g TID.

- **Acid-base disturbance**:
  • Identify type and precipitants.
  • Order ABG, calculate anion gap, check lactate, electrolytes.

- **Hyponatremia workup**:
  • Integrate existing labs; order missing: urine Na, osmolality, uric acid, serum osmolality, cortisol, TSH.

- **Hyponatremia management**:
  • Serial sodium monitoring; target correction 6–8 mEq/L over 24h.

- **CRRT initiation**:
  • Indications; plan CVVHDF @25cc/kg/hr; UF 0–100cc/hr; BMP q8h; daily phosphorus; med dosing; family discussion.

- **ESRD management**:
  • Dialysis schedule; specify access; outpatient HD plan.

- **Peritoneal dialysis prescription**:
  • Document home PD prescription: number of exchanges, fill volume, dwell time, bag type.

- **Anemia management**:
  • Check iron panel; administer ESA weekly (CKD) or on HD days (ESRD); transfuse if Hgb <7.

- **Bone mineral disorder management**:
  • Scan labs; order missing phosphorus/PTH; start binders; consider vitamin D analog.

- **Dialysis modality discussion**:
  • Discuss in-center vs home vs conservative dialysis; address patient concerns.

- **CRS management**:
  • Rationale: Scan echo for EF/diastolic dysfunction; review diuretic dosing and weight.
  • Context: If AKI triggered, note inability to start ACEi/ARB/ARNI/MRA/SGLT-2i.
  • Plan: Optimize diuretics, fluid management.

- **Hemodialysis initiation**:
  • **Rationale**: Identify acute indications: oliguria, refractory hyperkalemia, severe metabolic acidosis (pH <7.2), refractory volume overload, uremia (pericarditis, encephalopathy).
  • **Plan**: Initiate intermittent hemodialysis; discuss risks/complications (hypotension, cramps, arrhythmias); define prescription (blood flow rate, dialysate flow, duration); coordinate with HD unit.

- **<Other Trigger>**: Follow rules.
"""

# Streamlit UI
st.title("AI Note Writer for Nephrology Consultations")

# Inputs
reason = st.text_input("Reason for Consultation:")
hpi = st.text_area("HPI (2–3 sentences):", height=80)
labs = st.text_area("Labs (e.g., Cr, Na, K, Ca, PTH, Phos):", height=80)
request = st.text_area("Assessment & Plan (free text):", height=100)

if st.button("Generate Consultation Note"):
    combined = f"HPI:\n{hpi}\n\nLabs:\n{labs}\n\nRequest:\n{request}"
    resp1 = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role":"system","content":EXTRACTOR_SYSTEM}, {"role":"user","content":combined}],
        temperature=0
    )
    selected = json.loads(resp1.choices[0].message.content)
    ap_shorthand = "\n".join(f"{t}: {TRIGGERS[t]}" for t in selected)
    user_content = (
        f"**Reason for Consultation:** {reason}\n\n"
        f"**HPI:** {hpi}\n\n"
        f"**Labs:** {labs}\n\n"
        f"**Assessment & Plan:**\n{ap_shorthand}"
    )
    resp2 = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role":"system","content":GENERATOR_SYSTEM}, {"role":"user","content":user_content}],
        max_tokens=1200,
        temperature=0.7
    )
    st.subheader("Consultation Note")
    st.markdown(resp2.choices[0].message.content.strip())

# (Optional) dataset saving
