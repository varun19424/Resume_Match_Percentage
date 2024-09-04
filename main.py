import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import json
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Load environment variables
load_dotenv()

# Configure the Generative AI model
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to get the Gemini response from the Generative AI model
def get_gemini_response(input):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(input)
    return response.text

# Function to extract text from a PDF file
def input_pdf_text(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)
    text = ""
    for page in range(len(reader.pages)):
        text += reader.pages[page].extract_text()
    return text

# Function to save and export results as a PDF
def save_results_to_pdf(data, file_name):
    buffer = BytesIO()
    pdf_canvas = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    pdf_canvas.setFont("Helvetica", 12)
    y_position = height - 40

    pdf_canvas.drawString(30, y_position, "Resume Analysis Results")
    y_position -= 30

    for idx, result in enumerate(data):
        pdf_canvas.drawString(30, y_position, f"Job Description {idx + 1} Match Percentage: {result['JD Match']}%")
        y_position -= 20

        pdf_canvas.drawString(30, y_position, "Missing Keywords:")
        y_position -= 20
        for keyword in result["MissingKeywords"]:
            pdf_canvas.drawString(50, y_position, f"- {keyword}")
            y_position -= 20

        pdf_canvas.drawString(30, y_position, "Profile Summary:")
        y_position -= 20
        pdf_canvas.drawString(50, y_position, result["Profile Summary"])
        y_position -= 40

        # Adding page break if needed
        if y_position < 100:
            pdf_canvas.showPage()
            y_position = height - 40

    pdf_canvas.save()
    buffer.seek(0)
    return buffer

# Prompt Template
input_prompt_template = """
Hey, act like a skilled and experienced ATS (Applicant Tracking System) with a deep understanding of the tech field, software engineering, data science, data analysis, and big data engineering. Your task is to evaluate the resume based on the given job description. You must consider that the job market is very competitive and you should provide the best assistance for improving the resume. Assign the percentage of matching based on the job description and identify the missing keywords with high accuracy.

Resume: {text}
Job Description: {jd}

I want the response in one single string having the structure:
{{"JD Match":"%", "MissingKeywords":[], "Profile Summary":""}}
"""

# Streamlit app
st.title("Intelligent ATS")
st.text("Improve Your Resume ATS")

# User inputs multiple job descriptions
jd1 = st.text_area("Paste the First Job Description")
jd2 = st.text_area("Paste the Second Job Description (Optional)")
jd3 = st.text_area("Paste the Third Job Description (Optional)")
uploaded_file = st.file_uploader("Upload Your Resume", type="pdf", help="Please upload the PDF")

submit = st.button("Submit")

if submit:
    if uploaded_file is not None:
        try:
            # Extract text from the uploaded resume PDF
            resume_text = input_pdf_text(uploaded_file)

            # Initialize an empty list for storing results
            results = []

            # Loop through job descriptions and evaluate
            for jd in [jd1, jd2, jd3]:
                if jd:  # Skip if job description is empty
                    # Fill the input prompt with the resume text and job description
                    input_prompt = input_prompt_template.format(text=resume_text, jd=jd)

                    # Get the response from the Generative AI model
                    response = get_gemini_response(input_prompt)

                    # Parse the response JSON string to extract relevant information
                    response_data = json.loads(response)
                    results.append(response_data)

            # Display the results for each job description
            for idx, result in enumerate(results):
                st.subheader(f"Job Description {idx + 1} Match Percentage")
                st.write(f"{result['JD Match']}%")

                st.subheader(f"Missing Keywords for Job Description {idx + 1}")
                st.write(", ".join(result["MissingKeywords"]))

                st.subheader(f"Profile Summary for Job Description {idx + 1}")
                st.write(result["Profile Summary"])

                # Interactive Recommendations
                if result["MissingKeywords"]:
                    st.subheader("Interactive Recommendations")
                    for keyword in result["MissingKeywords"]:
                        st.write(f"Consider adding a project or experience related to '{keyword}' to your resume.")

            # Save and export results
            save_button = st.download_button(
                label="Download Results as PDF",
                data=save_results_to_pdf(results, "resume_analysis_results.pdf"),
                file_name="resume_analysis_results.pdf",
                mime="application/pdf"
            )

            # Feedback collection
            st.subheader("Feedback")
            feedback = st.text_area("Please provide your feedback here")
            if st.button("Submit Feedback"):
                # Handle feedback submission (e.g., save to a database or send via email)
                st.write("Thank you for your feedback!")

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
