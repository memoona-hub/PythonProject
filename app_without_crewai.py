import streamlit as st
import os
from PyPDF2 import PdfReader
from groq import Groq
from crewai import Agent, Task, Crew, Process, LLM
from fpdf import FPDF
from docx import Document
import io

GROQ_API_KEY= "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"
#GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if GROQ_API_KEY:
    print("GROQ_API_KEY is set.")
else:
    print("GROQ_API_KEY is not set.")
#-------------------------------------------------
# Title of the application
st.markdown(
    "<h1 style='text-align: center;'>E-Exam Generator</h1>",
    unsafe_allow_html=True
)

# Header
st.text("Upload a document and AI will generate mcqs and short questions for you!")

#-------------------------------------------------
# Step 1: Extract Text from PDF
def extract_text_from_pdf(uploaded_file):
    pdf_reader = PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text
#------------------------------------------------
# Step 2: Generate MCQs using Groq API
def generate_mcqs(text, num_questions=5):
    client = Groq(api_key=GROQ_API_KEY) # Now Groq is defined

    prompt = f"""
    Generate {num_questions} multiple-choice questions (MCQs) based on the following text:

    {text}

    Each question should have 4 options and one correct answer. Format the output as follows:

    Question 1: [Question text]
    A) [Option 1]
    B) [Option 2]
    C) [Option 3]
    D) [Option 4]
    Answer: [Correct option]

    Repeat for all questions.
    """

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates MCQs."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content
#------------------------------------------------
# Step 2: Generate short questions using Groq
def generate_short_questions(text, num_questions=5):
    client = Groq(api_key=GROQ_API_KEY) # Now Groq is defined

    prompt = f"""
    Generate {num_questions} short questions based on the following text:

    {text}

    Each question should has correct answer. Format the output as follows:

    Question 1: [Question text]
    Answer: [Correct answer]

    Repeat for all questions.
    """

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates short questions."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content
#------------------------------------------------
# Function to create a PDF file
def create_pdf(content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=content)
    return pdf.output(dest="S").encode("latin1")  # Return PDF as bytes

# Function to create a Word file
def create_word(content):
    doc = Document()
    doc.add_paragraph(content)
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()  # Return Word file as bytes

#------------------------------------------------
# start
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
if uploaded_file is not None:
    st.success("File uploaded successfully!")
    # Read the PDF file
    text = extract_text_from_pdf(uploaded_file)

    # Generate MCQs
    mcqs = generate_mcqs(text)
    #   st.write(mcqs)

    # Generate short questions
    short_questions = generate_short_questions(text)
    #   st.write(short_questions)

    # Radio button
    radio_option = st.radio("Choose generated file", ["mcqs", "short questions"])
    if radio_option == "short questions":
        # Selectbox
        option = st.selectbox("Save file as", ["Select an option","Word", "Pdf"])
        # st.write(f"You selected: {option}")
        if option == "Pdf":
            pdf_bytes = create_pdf(short_questions)
            st.download_button(
                label="Click to download PDF",
                data=pdf_bytes,
                file_name="generated_short_questions.pdf",
                mime="application/pdf",
            )

        if option == "Word":
            word_bytes = create_word(short_questions)
            st.download_button(
                label="Click to download Word",
                data=word_bytes,
                file_name="generated_short_questions.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
    if radio_option == "mcqs":
        # Selectbox
        option = st.selectbox("Save file as", ["Select an option","Word", "Pdf"])
        # st.write(f"You selected: {option}")
        if option == "Pdf":
            pdf_bytes = create_pdf(mcqs)
            st.download_button(
                label="Click to download PDF",
                data=pdf_bytes,
                file_name="generated_mcqs.pdf",
                mime="application/pdf",
            )

        if option == "Word":
            word_bytes = create_word(mcqs)
            st.download_button(
                label="Click to download Word",
                data=word_bytes,
                file_name="generated_mcqs.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
#------------------------------------------------
