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
2–3 concise sentences summarizing age, timeline, key events, and labs (include all labs provided).

**Assessment & Plan**  
For each trigger in the provided list, apply the following dynamic logic:

- **AKI**:
  • **Rationale**: Identify rise in creatinine from baseline; scan HPI and Labs for precipitants: volume overload (edema, weight gain), hypovolemia (vomiting/diarrhea), contrast exposure (dates), nephrotoxins (diuretics, ACEi/ARB, SGLT‑2i), obstruction (urinary retention, hydronephrosis). Weave these into one sentence.
  • **Workup**: Order renal ultrasound, UA, urine Na/Cl/Cr, quantify proteinuria, urine eosinophils unless already documented.
  • **Management**: Tailor to data: if hypovolemic → isotonic fluids; if overloaded → diuresis; always hold ACEi/ARB in AKI; monitor urine output and creatinine q8h.

- **AKI on CKD**:
  • **Rationale**: Similar to AKI, but phrase as "AKI on CKD" specifying baseline CKD stage and added precipitants.
  • **Plan**: As AKI, plus CKD-specific monitoring of GFR and nephrotoxin avoidance.

- **AKI workup** and **AKI management**: Apply the same workup/management sub‑sections as above when triggered individually.

- **Proteinuria workup**:
  • **Rationale**: Check for diabetes history (diabetes, HbA1c), autoimmune (SLE, vasculitis) and monoclonal (SPEP, free light chains).
  • **Plan**: Order ANA, ANCA, PLA2R, SPEP, free light chain ratio.

- **Hypercalcemia workup**:
  • **Rationale**: Note the calcium level and scan for symptoms (stones, bones, groans, psychiatric).
  • **Plan**: Order SPEP, PTH, PTHrP, free light chains, ACE level, vitamin D levels, CXR.

- **Hypercalcemia management**:
  • **Plan**: Administer IV fluids; give pamidronate 90 mg IV once; start calcitriol 4 IU/kg q12h; monitor calcium daily.

- **Hyperkalemia management**:
  • **Rationale**: Note potassium level and any ECG changes if provided.
  • **Plan**: Give IV calcium gluconate 2 g; insulin 10 U IV + D50; sodium bicarb 50 mEq IV; Lokelma 10 g TID; repeat K in 4h.

- **Acid-base disturbance**:
  • **Rationale**: Classify as high-AG, non-AG, lactic, or RTA; mention lab values.
  • **Plan**: Order ABG, calculate AG, check lactate/electrolytes; if non-AG or RTA, tailor bicarbonate therapy and monitor NaHCO3 use.

- **Hyponatremia workup**:
  • **Rationale**: Confirm Na<135; scan for volume status and labs.
  • **Plan**: Order urine Na/osmolality, serum osmolality, uric acid, cortisol, TSH.

- **Hyponatremia management**:
  • **Plan**: Serial Na monitoring; aim correction 6–8 mEq/L per 24h; consider D5W/ddavp if overcorrection risk.

- **CRRT initiation**:
  • **Rationale**: Indications (intractable fluid, electrolyte/acid‑base disorders, uremia).
  • **Plan**: CVVHDF @25 cc/kg/hr; UF 0–100 cc/hr; BMP q8h; daily phosphorus; adjust meds to eGFR 25–30; discuss risks/benefits.

- **ESRD management**:
  • **Plan**: Confirm MWF or TTS schedule; state access (AV fistula vs tunneled catheter); organize outpatient HD.

- **Peritoneal dialysis prescription**:
  • **Plan**: Document home PD regimen: exchanges/day, fill volume, dwell time, bag type per patient’s prescription.

- **Dialysis modality discussion**:
  • **Plan**: Compare in-center vs home vs conservative; address patient concerns.

- **Anemia management**:
  • **Rationale**: Note Hb; CKD vs ESRD context.
  • **Plan**: Check iron panel if missing; ESA weekly (CKD) or on HD days (ESRD); transfuse Hgb<7.

- **Bone mineral disorder management**:
  • **Rationale**: Note phosphorous/PTH lab values.
  • **Plan**: Order missing labs; start phosphate binders; consider vitamin D analog.

- **CRS management**:
  • **Rationale**: Integrate echo EF/diastolic dysfunction findings; weight trends; diuretic doses.
  • **Plan**: Use Bumex 2 mg IV BID; optimize fluid balance; note inability to start guideline meds if AKI present.

- **Hemodialysis initiation**:
  • **Rationale**: Identify acute indications: oliguria, refractory hyperkalemia/acidosis, volume overload, uremia.
  • **Plan**: Initiate intermittent HD; define blood/dialysate flow and duration; warn about hypotension, cramps; coordinate with HD unit.

Follow these rules to generate a concise, dynamic note for each triggered problem.
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

