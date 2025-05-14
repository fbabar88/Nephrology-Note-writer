import streamlit as st
import openai
import json

# Secure your API key in .streamlit/secrets.toml:
# OPENAI_API_KEY = "your_api_key_here"

# Configure OpenAI API
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Define canonical triggers (names only)
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

# Extractor: lists which triggers to include
EXTRACTOR_SYSTEM = f"""
You are a trigger-extraction assistant. Given a free-form user request, return a JSON array of exact trigger names chosen from this list:
{json.dumps(list(TRIGGERS.keys()))}
Only output the JSON array.
"""

# Generator: dynamic, paragraph-style rationale and plan
GENERATOR_SYSTEM = """
You are a board-certified nephrology consultant. Produce a note with the following sections:

**Reason for Consultation**  
<one-line reason>

**HPI**  
<verbatim HPI as entered by the user>

**Assessment & Plan**
For each triggered problem, write a concise paragraph that:
- Begins with the problem name followed by a colon (e.g., “AKI on CKD:”).
- Opens with the key HPI element relevant to that problem (e.g., “Anuric AKI following CTA contrast exposure…”).
- Integrates lab values directly in clinical shorthand, without parenthetical explanations or definitions.
- Combines workup and management descriptions in a single continuous paragraph using active verbs (e.g., “order renal ultrasound, hold diuretics, initiate HD”).
- Avoids first‑person phrases like “I will” or explanatory clauses like “also known as.”

Examples:

**AKI on CKD:** Anuric AKI after CTA contrast exposure and diuretic initiation with creatinine rising from 0.8 to 5.8, suggesting contrast‑induced ATN. Order renal ultrasound, urinalysis, urine Na/Cl/Cr and quantify proteinuria unless documented; hold HCTZ and Bystolic; initiate HD for anuria and monitor creatinine q8h.

**Hyperkalemia management:** Serum K 7.4 in AKI indicates impaired excretion. Administer IV calcium gluconate 2 g, insulin 10 U IV with D50, sodium bicarbonate 50 mEq IV, and Lokelma 10 g TID; repeat K in 4 h.

**Acid-base disturbance:** Bicarb 9 with AG ~20 in AKI. Order ABG and calculate AG; start HD to correct acidosis and monitor sodium bicarbonate therapy.

**CRS management:** Fluid overload in reduced EF heart failure with weight gain; optimize diuretics with Bumex 2 mg IV BID; monitor weight and urine output; hold ACEi/ARB in ongoing AKI.

Follow this format for all problems triggered.
"""
