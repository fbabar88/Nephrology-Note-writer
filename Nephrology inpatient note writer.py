 Install the OpenAI SDK if needed
!pip install openai

import openai
import ipywidgets as widgets
from IPython.display import display, HTML
import json

# Configure the OpenAI SDK for DeepSeek (Beta Endpoint)
openai.api_base = "https://api.deepseek.com/beta"  # Use the beta endpoint
openai.api_key = ""  # Replace with your DeepSeek API key

# Global variables to store generated outputs and dataset entries
current_generated_note = ""
current_soap_note = ""
dataset_entries = []

##############################################
# Section 1: Generate Consultation Note
##############################################

# Input widgets for the consultation note with empty default values
reason_widget = widgets.Text(
    value="",
    description="Reason for Consultation:",
    placeholder="Enter reason for consultation"
)

symptoms_widget = widgets.Textarea(
    value="",
    description="Presenting Symptoms:",
    placeholder="Enter key symptoms",
    layout=widgets.Layout(width='100%', height='80px')
)

context_widget = widgets.Textarea(
    value="",
    description="Clinical History & Context:",
    placeholder="Enter any relevant clinical history and context",
    layout=widgets.Layout(width='100%', height='80px')
)

labs_widget = widgets.Textarea(
    value="",
    description="Labs:",
    placeholder="Enter key lab values",
    layout=widgets.Layout(width='100%', height='80px')
)

# New combined input for targeted Assessment and Plan
assessment_plan_widget = widgets.Textarea(
    value="",
    description="Assessment & Plan:",
    placeholder=("Enter a combined list of problem headings and corresponding treatment options. "
                 "For example:\n"
                 "AKI: Optimize fluid management, avoid nephrotoxic agents, consider RRT if indicated.\n"
                 "Metabolic Acidosis: Monitor acid-base status, administer bicarbonate if pH < 7.2.\n"
                 "Cardiogenic Shock: Adjust pressor support and collaborate with cardiology."),
    layout=widgets.Layout(width='100%', height='150px')
)

# Display the input widgets
display(reason_widget)
display(symptoms_widget)
display(context_widget)
display(labs_widget)
display(assessment_plan_widget)

# Button to generate consultation note
generate_button = widgets.Button(description="Generate Consultation Note")
display(generate_button)

# Placeholder for feedback widgets (if needed)
feedback_area = widgets.VBox([])
display(feedback_area)

def generate_consultation_note(b):
    global current_generated_note
    
    # Retrieve input values
    reason = reason_widget.value
    symptoms = symptoms_widget.value
    context_history = context_widget.value
    labs = labs_widget.value
    assessment_plan_input = assessment_plan_widget.value

    # Construct the prompt for the consultation note
    prompt = f"""
Generate a comprehensive Epic consultation note in the style of a board-certified nephrologist using the following inputs:

**Reason for Consultation:**
{reason}

**Presenting Symptoms:**
{symptoms}

**Clinical History & Context:**
{context_history}

**Labs:**
{labs}

**Assessment & Plan (Targeted):**
{assessment_plan_input}

Based on the above, generate a note that includes:
1. **Reason for Consultation:** Restate the consultation reason.
2. **History of Present Illness (HPI):** Provide a concise narrative summarizing the presenting symptoms, clinical history & context, and labs.
3. **Assessment and Plan:** For each problem mentioned in the 'Assessment & Plan' input, elaborate a brief assessment using clinical details from the HPI and then integrate the corresponding targeted treatment options.
Do not add any extra summary sections.
"""
    # Call the DeepSeek API for the consultation note
    response = openai.Completion.create(
        model="deepseek-chat",
        prompt=prompt,
        max_tokens=1200,
        temperature=0.7,
    )
    
    generated_note = response.choices[0].text.strip()
    current_generated_note = generated_note  # Store it globally

    # Display the generated consultation note in a read-only Textarea widget
    note_textarea = widgets.Textarea(
        value=generated_note,
        description="Consultation Note:",
        layout=widgets.Layout(width='100%', height='600px'),
        disabled=True
    )
    display(note_textarea)

generate_button.on_click(generate_consultation_note)

##############################################
# Section 2: Generate SOAP Note from Consultation Note with Case Update
##############################################

# Input widget for the comprehensive case update (reflecting interval changes)
case_update_widget = widgets.Textarea(
    value="",
    description="Case Update:",
    placeholder="Enter a comprehensive update on the case",
    layout=widgets.Layout(width='100%', height='150px')
)
display(case_update_widget)

# Button to generate the SOAP note
soap_button = widgets.Button(description="Generate SOAP Note")
display(soap_button)

def generate_soap_note(b):
    global current_soap_note
    # Check if a consultation note exists
    if not current_generated_note:
        display(HTML("<b>Please generate a consultation note first.</b>"))
        return

    # Retrieve the case update text
    case_update = case_update_widget.value

    # Construct the transformation prompt for the SOAP note
    soap_prompt = f"""
Using the following consultation note and case update, generate a SOAP note for a progress note in the style of a board-certified nephrologist.
In the SOAP note:
- **Subjective:** Provide a concise statement of the patient's current condition using the case update.
- **Assessment and Plan:** Reflect the problem list and treatment options as provided in the consultation note.
- **Objective:** Omit this section.

Consultation Note:
{current_generated_note}

Case Update:
{case_update}

SOAP Note:
"""
    # Call the DeepSeek API for the SOAP note transformation
    response = openai.Completion.create(
        model="deepseek-chat",
        prompt=soap_prompt,
        max_tokens=800,
        temperature=0.7,
    )
    
    soap_note = response.choices[0].text.strip()
    current_soap_note = soap_note  # Store it globally

    # Display the generated SOAP note in a read-only Textarea widget
    soap_note_area = widgets.Textarea(
        value=soap_note,
        description="SOAP Note:",
        layout=widgets.Layout(width='100%', height='600px'),
        disabled=True
    )
    display(soap_note_area)

soap_button.on_click(generate_soap_note)

##############################################
# Section 3: Dataset Collection for Fine-Tuning
##############################################

# Button to save the current input and output as a dataset entry
save_dataset_button = widgets.Button(description="Save Entry to Dataset")
display(save_dataset_button)

def save_dataset_entry(b):
    global dataset_entries, current_generated_note, current_soap_note
    entry = {
        "reason_for_consultation": reason_widget.value,
        "presenting_symptoms": symptoms_widget.value,
        "clinical_history_context": context_widget.value,
        "labs": labs_widget.value,
        "assessment_plan_input": assessment_plan_widget.value,
        "consultation_note": current_generated_note,
        "case_update": case_update_widget.value,
        "soap_note": current_soap_note
    }
    dataset_entries.append(entry)
    display(HTML("<b>Entry saved to dataset!</b>"))

save_dataset_button.on_click(save_dataset_entry)

# Button to download the dataset as a JSONL file
download_dataset_button = widgets.Button(description="Download Dataset")
display(download_dataset_button)

def download_dataset(b):
    filename = "fine_tuning_dataset.jsonl"
    with open(filename, "w") as f:
        for entry in dataset_entries:
            json.dump(entry, f)
            f.write("\n")
    from google.colab import files
    files.download(filename)

download_dataset_button.on_click(download_dataset)
