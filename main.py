import streamlit as st  # for the website 
import time
import pandas as pd
import numpy as np
from datetime import datetime
import os 
import openai  # for the chatbot
from openai import OpenAI  # for the chatbot
import PyPDF2  # to extract text from PDFs
import re

if 'history' not in st.session_state:
    st.session_state.history = []
if 'form_data' not in st.session_state:
    st.session_state.form_data = {}

client = OpenAI(api_key="")

def generate_autograde_feedback(user_data, pdf_text=""):
    prompt = f"""
As an autograder, please provide detailed feedback on the following assignment submission.

ASSIGNMENT DETAILS:
- Subject: {user_data["subject"]}
- Education Level: {user_data["education_level"]}
- Purpose of Assignment: {user_data["purpose"]}
- Correctness Weight: {user_data["correctness"]}%
- Explanation Weight: {user_data["explanation"]}%
- Answer Format: {user_data["answer_format"]}

Provide positive areas in 2 bullets.
Then provide what could be improved on in 3 bullets. If there is an error within what the user gave such as an answer or explanation, one of these bullets should address this error.
At the end of your response, on a new line, please include: "Final Grade: XX/100" (where XX is the numerical grade out of 100).

"""
    if pdf_text:
        prompt += f"\nAssignment Content (extracted from uploaded PDF):\n{pdf_text}\n"
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an experienced educator and autograder. Provide detailed feedback and assign points based on the assignment details. Ensure to include a final numerical grade as specified."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating feedback: {str(e)}")
        return "Unable to generate feedback at this time. Please try again later."

def save_to_history(user_data, feedback):
    st.session_state.history.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "subject": user_data["subject"],
        "education_level": user_data["education_level"],
        "feedback": feedback
    })

def display_feedback(feedback):
    st.subheader("Assignment Feedback")
    st.markdown(feedback)

    # Extract the final grade from feedback using regex
    final_grade = None
    match = re.search(r"Final Grade:\s*(\d+)", feedback)
    if match:
        final_grade = match.group(1)

    if final_grade:
        # Display the final grade prominently in large text
        st.markdown(f"<h1 style='text-align: center;'>Final Grade: {final_grade}/100</h1>", unsafe_allow_html=True)

    st.download_button(
        label="Download Feedback as Text",
        data=feedback,
        file_name="assignment_feedback.txt",
        mime="text/plain"
    )

st.set_page_config(page_title="Autograder", page_icon="📚", layout="wide")

st.title("AssessAI Autograder")
st.write("This tool provides **automated feedback** and assigns points based on your assignment submission. ")

col1, col2 = st.columns(2)

with col1:
    # Subjects with emojis
    subject = st.selectbox(
        "Subject",
        ["Mathematics 📐", "English 📚", "History 🏺", "Science 🔬", "Art 🎨", "Other"],
        index=0
    )
    if subject == "Other":
        subject_other = st.text_input("Please specify the subject", st.session_state.form_data.get("subject_other", ""))
    else:
        subject_other = ""

    # Changed grade input to education level select box
    education_level = st.selectbox(
        "Education Level",
        ["Elementary School", "Middle School", "High School", "University", "Bachelors degree", "Masters degree", "Postgraduate"],
        index=2
    )
    # Extend purpose text area height for longer input
    purpose = st.text_area("Purpose of the Assignment", st.session_state.form_data.get("purpose", ""), height=150)

    # Add sliders for importance weights
    correctness = st.slider("Correctness Weight (%)", 0, 100, 50, step=1)
    explanation = st.slider("Explanation Weight (%)", 0, 100, 50, step=1)



with col2:
    
    file_upload = st.file_uploader("Upload Assignment (PDF or Image)", type=["pdf", "png", "jpg", "jpeg"])
    # Answer Format input
    answer_format = st.selectbox(
        "Answer Format",
        ["MCQ", "FRQ", "Code Submission", "Essay", "Short Answer"],
        index=0
    )
if st.button("Generate Feedback"):
    if not purpose:
        st.error("Please enter the purpose of the assignment.")
    elif not file_upload:
        st.error("Please upload a file (PDF or Image).")
    else:
        subject_final = subject_other if subject == "Other" else subject
        st.session_state.form_data = {
            "subject": subject_final,
            "education_level": education_level,
            "purpose": purpose,
            "correctness": correctness,
            "explanation": explanation,
            "answer_format": answer_format
        }

        pdf_text = ""
        # Process PDF file if uploaded and if its type is PDF
        if file_upload is not None and file_upload.type == "application/pdf":
            try:
                pdf_reader = PyPDF2.PdfReader(file_upload)
                for page in pdf_reader.pages:
                    pdf_text += page.extract_text() + "\n"
            except Exception as e:
                st.error(f"Error reading PDF file: {str(e)}")

        with st.spinner("Generating feedback..."):
            time.sleep(1)
            feedback = generate_autograde_feedback(st.session_state.form_data, pdf_text)
            save_to_history(st.session_state.form_data, feedback)
            display_feedback(feedback)
        st.success("Feedback generated successfully.")

st.markdown("---")
st.markdown("""
**IMPORTANT DISCLAIMER**: This autograder provides automated feedback and should not replace human evaluation.
""")
