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

# Create the trigger list once
TRIGGER_LIST = list(TRIGGERS.keys())

# Modified extraction prompt to include lab interpretation
EXTRACTOR_SYSTEM = """
You are a medical note analysis assistant. Given a free-form medical note:
1. Return a JSON object containing:
   - "sections": array of objects with:
     - "heading": the original section heading from the text
     - "content": the content under that heading
     - "related_triggers": array of related trigger names from the predefined trigger list
   - "lab_interpretation": brief interpretation of any lab trends or abnormalities
2. Preserve the original section headings exactly as written.
3. Map the content to relevant triggers while maintaining the original organization.
"""

# Modified generation prompt
GENERATOR_SYSTEM = """
You are a board-certified nephrology AI assistant. Compose a complete consultation note using the sections below, in this exact order:

**Reason for Consultation**
Use the reason text provided as a single line.

**HPI**
Create a detailed narrative that:
- Incorporates lab values and trends naturally into the story
- Highlights significant lab abnormalities and their progression
- Connects lab findings to clinical presentation
- Maintains chronological flow

**Labs**
List the key lab values as provided, organized by:
- Kidney function
- Electrolytes
- Acid-base status
- Other relevant labs

**Assessment & Plan**
1. Use the EXACT section headings provided in the input
2. Reference relevant lab values in your assessment
3. Incorporate relevant workup and management details from triggers
4. Use direct imperative phrasing for all recommendations
5. Ensure each section is comprehensive and well-organized
"""

# Define extraction function schema
extract_fn = {
    "name": "extract_content",
    "description": "Extract sections and map to triggers while preserving original headings",
    "parameters": {
        "type": "object",
        "properties": {
            "sections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "heading": {"type": "string"},
                        "content": {"type": "string"},
                        "related_triggers": {
                            "type": "array",
                            "items": {"type": "string", "enum": TRIGGER_LIST}
                        }
                    },
                    "required": ["heading", "content", "related_triggers"]
                }
            }
        },
        "required": ["sections"]
    }
}

# Streamlit UI
st.title("AI Note Writer for Nephrology Consultations")

reason = st.text_input("Reason for Consultation:")

# Split lab input into current and trending
st.subheader("Laboratory Data")
col1, col2 = st.columns(2)
with col1:
    current_labs = st.text_area("Current Labs:", height=120, 
                               help="Enter current lab values (e.g., Cr 2.4, Na 138, K 5.2)")
with col2:
    trending_labs = st.text_area("Trending Labs:", height=120,
                                help="Enter relevant lab trends (e.g., Cr 1.2→2.4→3.1 over 3 days)")

hpi_context = st.text_area("HPI Context:", height=100,
                          help="Enter relevant history, timeline, and clinical context")

assessment_plan = st.text_area("Assessment & Plan:", height=200,
                             help="Enter your assessment and plan with your preferred section headings")

if st.button("Generate Consultation Note"):
    # 1) Extract sections and related triggers
    with st.spinner("Processing input..."):
        resp1 = openai.ChatCompletion.create(
            model="gpt-4-0613",
            messages=[
                {"role": "system", "content": EXTRACTOR_SYSTEM},
                {"role": "user", "content": assessment_plan}
            ],
            functions=[extract_fn],
            function_call={"name": "extract_content"},
            temperature=0
        )
        content = json.loads(resp1.choices[0].message.function_call.arguments)
        sections = content["sections"]

    # 2) Generate HPI with lab integration
    with st.spinner("Generating HPI..."):
        hpi_content = f"""
Context: {hpi_context}
Current Labs: {current_labs}
Trending Labs: {trending_labs}
"""
        hpi_response = openai.ChatCompletion.create(
            model="gpt-4-0613",
            messages=[
                {"role": "system", "content": GENERATOR_SYSTEM},
                {"role": "user", "content": hpi_content}
            ],
            temperature=0.7,
            max_tokens=800
        )
        generated_hpi = hpi_response.choices[0].message.content.strip()

    # 3) Generate final note
    if not sections:
        st.error("No valid sections found. Please check your input.")
    else:
        sections_content = "\n\n".join(
            f"SECTION: {section['heading']}\n"
            f"CONTENT: {section['content']}\n"
            f"TRIGGERS: {', '.join(section['related_triggers']) if section['related_triggers'] else 'None'}"
            for section in sections
        )
        
        user_content = (
            f"**Reason for Consultation:** {reason}\n\n"
            f"**HPI:** {generated_hpi}\n\n"
            f"**Current Labs:** {current_labs}\n"
            f"**Trending Labs:** {trending_labs}\n\n"
            f"**Assessment & Plan Sections:**\n{sections_content}\n\n"
            f"**Original Text:**\n{assessment_plan}"
        )

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
