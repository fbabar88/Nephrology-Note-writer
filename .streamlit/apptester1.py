    with tab2:
        st.subheader("Generate SOAP Note")
        case_update = st.text_area("Case Update:", "Enter a comprehensive update on the case", height=150, key="case_update_input")
        if st.button("Generate SOAP Note", key="generate_soap"):
            if not patient_record.get("consultation_note"):
                st.error("Please generate a consultation note first.")
            else:
                soap_prompt = f"""
Using the following consultation note and case update, generate a SOAP note for a progress note in the style of a board-certified nephrologist.
In the SOAP note:
- **Subjective:** Provide a concise statement of the patient's current condition using the case update.
- **Assessment and Plan:** Reflect the problem list and treatment options as provided in the consultation note.
- **Objective:** Omit this section.

Consultation Note:
{patient_record.get("consultation_note")}

Case Update:
{case_update}
"""  # <-- Added closing triple-quote here
                with st.spinner("Generating SOAP Note..."):
                    response = openai.Completion.create(
                        model="deepseek-chat",
                        prompt=soap_prompt,
                        max_tokens=800,
                        temperature=0.5,
                    )
                    soap_note = response.choices[0].text.strip()
                    soap_note = remove_leading_asterisks(soap_note)
                    patient_record["soap_note"] = soap_note
                    patient_record["note_type"] = "Progress"
                    patient_record["last_updated"] = str(datetime.datetime.now())
                    st.success("SOAP note generated and saved!")
                    st.text_area("SOAP Note:", value=soap_note, height=400, key="soap_note_display")

    with tab3:
        st.subheader("Generate Follow-Up Update")
        new_update = st.text_area("Enter New Update (one-liner):", "Provide a one-liner update...", height=68, key="new_update_input")
        if st.button("Generate Follow-Up Note", key="generate_followup"):
            if patient_record.get("soap_note"):
                base_note = patient_record.get("soap_note")
            else:
                base_note = patient_record.get("consultation_note")
            followup_prompt = f"""
Using the following previous SOAP note and the new one-liner update, generate an updated follow-up SOAP note for a progress note in the style of a board-certified nephrologist.

Instructions:
- In the Subjective section, include only a concise one-liner summarizing the new update.
- Do not repeat the full history of present illness.
- In the Assessment and Plan section, integrate the new update with the existing plan.

Previous SOAP Note:
{base_note}

New Update (one-liner):
{new_update}

Generate an updated SOAP note that reflects only the new update in the Subjective section and integrates it into the Assessment and Plan.
"""
            with st.spinner("Generating Follow-Up Note..."):
                response = openai.Completion.create(
                    model="deepseek-chat",
                    prompt=followup_prompt,
                    max_tokens=600,
                    temperature=0.5,
                )
                new_soap_note = response.choices[0].text.strip()
                new_soap_note = remove_leading_asterisks(new_soap_note)
                patient_record["soap_note"] = new_soap_note
                patient_record["note_type"] = "Progress"
                patient_record["last_updated"] = str(datetime.datetime.now())
                st.success("Follow-Up note generated and saved!")
                st.text_area("Updated Follow-Up SOAP Note:", value=new_soap_note, height=400, key="followup_display")

    if st.button("Save Patient Record to S3", key="save_patient_record"):
        upload_patient_record_to_s3(patient_record)
        st.json(patient_record)
