import streamlit as st
import os
from PyPDF2 import PdfReader
import groq
from crewai import Agent, Task, Crew, Process, LLM
from fpdf import FPDF
from docx import Document
import io
from litellm import completion
from crewai.tools import BaseTool
import re

GROQ_API_KEY= "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"

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

#--------------------------------------------------
# Custom LLM class for Groq
class LiteLLM:
    def __init__(self, model_name="groq/llama3-8b-8192", api_key=GROQ_API_KEY):
        self.model_name = model_name
        self.api_key = api_key

    def generate(self, prompt: str) -> str:
        """
        Generate a response using LiteLLM.

        Args:
            prompt (str): The input prompt for the model.

        Returns:
            str: The model's response.
        """
        try:
            response = completion(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                api_key=self.api_key
            )
            # Check for empty or invalid response
            if not response or not response.choices:
                return "Error: Empty or invalid response from the LLM+++++."
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"

# Initialize the Groq LLM
groq_llm = LiteLLM(model_name="groq/llama3-8b-8192", api_key=GROQ_API_KEY)
#response = groq_llm.generate("Hello, how are you?")
#st.write(response)

#------------------------------------------------Functions & Crew

# Step 1: Extract Text from PDF
def extract_text_from_pdf(uploaded_file):
    pdf_reader = PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# text cleaning
def preprocess_text(text):
    # Remove extra spaces and newlines
    text = re.sub(r'\s+', ' ', text).strip()
    return text

#------------------------------------------------
# Function to create a PDF file to download
def create_pdf(content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=content)
    return pdf.output(dest="S").encode("latin1")  # Return PDF as bytes
#----------------------------------------------
# Function to create a Word file to download
def create_word(content):
    doc = Document()
    doc.add_paragraph(content)
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()  # Return Word file as bytes

#------------------------------------------------Crew
# Step 3: CrewAI Agents
def create_crewai_agents(pdf_text):
# Define Agents
    mcq_agent = Agent(
        name="mcq generator Agent",
        role="MCQ Creator",
        goal="Generate multiple-choice questions (MCQs) based on the provided text",
        backstory="A skilled question creator with a passion for education and assessment.",
        llm=groq_llm  # Use the custom Groq LLM
    )
    short_question_agent = Agent(
        name="short questions generator Agent",
        role="Short Questions Creator",
        goal="Generate short questions and answers based on the provided text.",
        backstory="A skilled question creator with a passion for education and assessment.",
        llm=groq_llm  # Use the custom Groq LLM
    )
# Define Tasks
    mcq_task = Task(
        description=f"Generate 5 multiple-choice questions (MCQs) based on \n\n{pdf_text}",
        agent=mcq_agent,
        expected_output="A list of 5 MCQs with 4 options each and the correct answer.",
 #       context=[{"document_text": pdf_text}]  # Pass the PDF text as a dictionary inside a list
    )
    short_question_task = Task(
        description=f"Generate 5 short questions and answers based on \n\n{pdf_text}",
        agent=short_question_agent,
        expected_output="A list of 5 short questions and answers each."
    )

# Create Crew
    crew = Crew(
        agents=[mcq_agent,short_question_agent],
        tasks=[mcq_task,short_question_task]
    )
    # Execute the crew's tasks
    results = crew.kickoff()

    # Print the results
    return results

#------------------------------------------------main starts
#container = st.container(border=True)
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
if uploaded_file is not None:
    st.success("File uploaded successfully!")
    # Read the PDF file
    pdf_text = extract_text_from_pdf(uploaded_file)
    print("Text extraction complete.\n")

    # text cleaning
    cleaned_text = preprocess_text(pdf_text)
    print("Cleaned Text:", cleaned_text[:500])
    print("Text cleaning complete.\n")

    results = create_crewai_agents(cleaned_text)
    print(results)
    mcqs= results.tasks_output[0].raw
    short_questions = results.tasks_output[1].raw
#    short_questions = "test"
#    for idx, result in enumerate(results.tasks_output):
#        st.write(f"Task {idx + 1} Output:\n{result}\n")
    # Radio button
    radio_option = st.radio("Choose generated file", ["mcqs", "short questions"])

    if radio_option == "short questions":
        # Selectbox
        option = st.selectbox("Save file as", ["Select an option", "Word", "Pdf"])
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
        option = st.selectbox("Save file as", ["Select an option", "Word", "Pdf"])
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
# ------------------------------------------------