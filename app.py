import os
import streamlit as st
import pandas as pd
import csv
from contextlib import redirect_stdout
from io import StringIO
from dotenv import load_dotenv
import google.generativeai as genai
import matplotlib.pyplot as plt

# Load environment variables
load_dotenv()

# Configure Genai Key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to load Google Gemini Model and provide queries as a response
def get_gemini_response(question, prompt):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content([prompt, question])
    return response.text

# Function to process multiple uploaded files and extract column names
def get_column_names_from_file(uploaded_files):
    column_names = {}
    for file in uploaded_files:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith('.xlsx'):
            df = pd.read_excel(file)
        elif file.name.endswith('.xls'):
            df = pd.read_excel(file, engine='xlrd')  # Use xlrd for .xls files
        else:
            st.error(f"Unsupported file format: {file.name}")
            continue
        column_names[file.name] = df.columns.tolist()
    return column_names
# Function to clean up the generated code by removing Markdown code block delimiters
def clean_generated_code(code):
    # Remove Markdown code block delimiters
    cleaned_code = code.replace('```python', '').replace('```', '').strip()
    return cleaned_code
## Define Prompt Template for Python Code Generation
prompt_template = """
You are an expert Python developer. Your task is to generate Python code based on English questions about the following uploaded data files. Here are the files and their columns:

{file_column_info}


The generated Python code should be correct, concise, and without comments.
"""

# Streamlit App
st.set_page_config(page_title="Text to Python Code Generator")
st.header("Python Code Generator from Natural Language Queries")

# Initialize session state to store chat history
if "messages" not in st.session_state:
    st.session_state.messages = []



# File uploader for multiple files
uploaded_files = st.file_uploader("Upload CSV/Excel files", accept_multiple_files=True)

if uploaded_files:
    # Extract column names from uploaded files
    column_names = get_column_names_from_file(uploaded_files)
    
    # Prepare the file-column info for the prompt
    file_column_info = "\n".join([f"{file_name}: {', '.join(columns)}" for file_name, columns in column_names.items()])

    # Inject file and column information into the prompt
    prompt = prompt_template.format(file_column_info=file_column_info)

    # Input for user query
    question = st.text_input("Ask a question about your data", key="input")

    # Submit button
    submit = st.button("Generate Python Code")

    # If submit button is clicked
    if submit:
        if question:
            response = get_gemini_response(question, prompt)
            print(response)
            st.subheader("Generated Python Code:")
            # Clean the generated code
            cleaned_code = clean_generated_code(response)
            
            st.code(cleaned_code)
            # Append user query, response to chat history
            st.session_state.messages.append({"role": "user", "content": question})
            st.session_state.messages.append({"role": "response_python_code", "content": response})
        else:
            st.error("Please enter a valid question.")
