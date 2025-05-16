import streamlit as st
import openai
import json
import re

# [Previous TRIGGERS dictionary remains the same]

# Add lab value processing helper
def parse_lab_values(lab_text):
    """Extract and structure lab values for easier reference"""
    lab_dict = {}
    if not lab_text:
        return lab_dict
    
    # Common lab patterns
    patterns = {
        'creatinine': r'(?i)(?:Cr|Creat)(?:inine)?\s*(?:of|is|:|\s)\s*(\d+\.?\d*)',
        'sodium': r'(?i)(?:Na|Sodium)\s*(?:of|is|:|\s)\s*(\d+\.?\d*)',
        'potassium': r'(?i)(?:K|Potassium)\s*(?:of|is|:|\s)\s*(\d+\.?\d*)',
        'calcium': r'(?i)(?:Ca|Calcium)\s*(?:of|is|:|\s)\s*(\d+\.?\d*)',
        'phosphorus': r'(?i)(?:Phos|Phosphorus)\s*(?:of|is|:|\s)\s*(\d+\.?\d*)',
        'bicarbonate': r'(?i)(?:HCO3|Bicarb)\s*(?:of|is|:|\s)\s*(\d+\.?\d*)',
        'bun': r'(?i)(?:BUN)\s*(?:of|is|:|\s)\s*(\d+\.?\d*)',
    }
    
    for lab, pattern in patterns.items():
        match = re.search(pattern, lab_text)
        if match:
            lab_dict[lab] = float(match.group(1))
    
    return lab_dict

# Enhanced HPI generation prompt
HPI_SYSTEM = """
You are a nephrology AI assistant crafting detailed HPIs. Create a comprehensive HPI that:
1. Begins with patient demographics and chief complaint
2. Incorporates relevant lab trends, emphasizing:
   - Kidney function (Cr, BUN)
   - Electrolytes (Na, K, Ca, Phos)
   - Acid-base status (HCO3)
3. Describes the timeline of events
4. Includes relevant medical history and medications
5. Maintains a clear narrative flow

Format lab values naturally within sentences, e.g.:
"The patient's creatinine increased from 1.2 to 3.4 mg/dL over 48 hours, accompanied by hyperkalemia (K 5.8 mEq/L)."
"""

# Modified extraction prompt to include lab interpretation
EXTRACTOR_SYSTEM = f"""
You are a medical note analysis assistant. Given a free-form medical note:
1. Return a JSON object containing:
   - "sections": array of objects with:
     - "heading": the original section heading from the text
     - "content": the content under that heading
     - "related_triggers": array of related trigger names from this master list: {json.dumps(list(TRIGGERS.keys()))}
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

# [Previous extract_fn remains the same]

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
    # 1) Process lab data
    current_lab_values = parse_lab_values(current_labs)
    trending_lab_values = trending_labs  # Keep as text for narrative processing

    # 2) Extract sections and related triggers
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

    # 3) Generate HPI with lab integration
    with st.spinner("Generating HPI..."):
        hpi_content = f"""
Context: {hpi_context}
Current Labs: {current_labs}
Trending Labs: {trending_labs}
"""
        hpi_response = openai.ChatCompletion.create(
            model="gpt-4-0613",
            messages=[
                {"role": "system", "content": HPI_SYSTEM},
                {"role": "user", "content": hpi_content}
            ],
            temperature=0.7,
            max_tokens=800
        )
        generated_hpi = hpi_response.choices[0].message.content.strip()

    # 4) Generate final note
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
