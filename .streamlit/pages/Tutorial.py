import streamlit as st

st.title("Nephrology Note Writer Tutorial")

st.write("""
Welcome to the **Nephrology Note Writer App**! This tutorial will guide you through the various functionalities of the app so that you can generate comprehensive, evidence‐based progress notes efficiently.

The app supports two input modes:
- **Structured Input:** Enter detailed information (e.g., symptoms, labs, history) via individual fields.
- **Free Text:** Use one large text box for quicker note entry when time is short.
""")

st.header("1. Getting Started")
st.markdown("""
- **Timer:**  
  Click the **Start Timer** button in the sidebar to begin tracking your data entry time.
  
- **Visit Type & Condition:**  
  Use the sidebar controls to select the visit type (e.g., New Patient, Follow-Up) and the relevant condition (e.g., CKD, Hypertension). This selection tailors the input fields and guideline recommendations.
""")

st.header("2. Input Modes")
st.markdown("""
**Structured Input Mode:**  
- Fill out individual fields for key details such as:
  - Reason for Visit
  - Symptoms or HPI (History of Present Illness)
  - Lab data
  - Additional comments or risk factors  
- This mode is ideal when you have time to provide detailed information.

**Free Text Mode:**  
- Use a single, large text box to quickly enter all necessary information.  
- This option is perfect when you need to document rapidly without filling multiple fields.
""")

st.header("3. Generating the Progress Note")
st.markdown("""
- **Generate Note:**  
  After entering your data, click the **Generate Progress Note** button. The app sends your input (plus guideline recommendations) to the DeepSeek API to generate a comprehensive note.
  
- **Review & Edit:**  
  The generated note will appear in an editable text area, allowing you to review and make any adjustments before finalizing.
  
- **Download:**  
  Use the **Download Note** button to save the final note as a text file.
""")

st.header("4. Resetting the Form")
st.markdown("""
- **Reset Form:**  
  If you need to clear all your inputs and start over, click the **Reset Form** button in the sidebar. This will clear the session state and reload the app.
  
  *Tip:* If you encounter any issues with resetting, ensure your Streamlit version is up-to-date.
""")

st.header("5. Tips & Troubleshooting")
st.markdown("""
- **Incomplete Notes:**  
  If the generated note appears cut off or incomplete, consider adjusting the API's `max_tokens` parameter or shortening the prompt.
  
- **Guideline Recommendations:**  
  The app appends guideline recommendations (loaded from a JSON file) to ensure the note is evidence-based.
  
- **Streamlit Issues:**  
  For any errors or performance issues, check the logs via Streamlit Cloud’s 'Manage app' section.
""")

st.write("""
**Feedback and Support:**  
If you have any questions or need further assistance, please contact the support team or the app developer. Enjoy using the Nephrology Note Writer App!
""")
