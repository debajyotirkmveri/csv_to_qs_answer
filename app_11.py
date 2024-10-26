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

# Function to clean up the generated code by removing Markdown code block delimiters
def clean_generated_code(code):
    cleaned_code = code.replace('```python', '').replace('```', '').strip()
    return cleaned_code

# Function to append data to a CSV file
def append_to_csv(data, csv_file_path):
    file_exists = os.path.exists(csv_file_path)
    
    with open(csv_file_path, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        if not file_exists:
            writer.writerow(["Question", "Generated Query", "Answer"])
        
        writer.writerow(data)

# Function to save the uploaded file to a folder
def save_uploaded_file(uploaded_file, folder='uploaded_files'):
    if not os.path.exists(folder):
        os.makedirs(folder)
    file_path = os.path.join(folder, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

# Streamlit App
st.set_page_config(page_title="Text to DataFrame Query")
st.header("DataFrame Query Chatbot")

# Initialize session state to store chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f"**User:** {message['content']}")
    elif message["role"] == "response_dataframe_query":
        st.markdown(f"**Response DataFrame Query:** {message['content']}")

# Upload multiple Excel or CSV files
uploaded_files = st.file_uploader("Choose Excel or CSV files", type=['xlsx', 'csv'], accept_multiple_files=True)

# DataFrames dictionary to hold each sheet's DataFrame
dfs = {}
column_names = {}
file_paths = []
file_types = {}  # Store file types for each sheet

# Process each uploaded file
for uploaded_file in uploaded_files:
    if uploaded_file is not None:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == 'xlsx':
            file_path = save_uploaded_file(uploaded_file)
            file_paths.append(file_path)
            xls = pd.ExcelFile(file_path)
            sheet_names = xls.sheet_names
            
            for sheet_name in sheet_names:
                df = pd.read_excel(xls, sheet_name)
                dfs[sheet_name] = df
                column_names[sheet_name] = df.columns.tolist()
                file_types[sheet_name] = 'excel'
                st.write(f"DataFrame for {sheet_name}:")
                st.dataframe(df)
        
        elif file_extension == 'csv':
            file_path = save_uploaded_file(uploaded_file)
            file_paths.append(file_path)
            df = pd.read_csv(file_path)
            sheet_name = uploaded_file.name
            dfs[sheet_name] = df
            column_names[sheet_name] = df.columns.tolist()
            file_types[sheet_name] = 'csv'
            st.write(f"DataFrame for {sheet_name}:")
            st.dataframe(df)

# Input for user query
question = st.text_input("Input: Ask the question", key="input")

# Define the prompt template for joining datasets
prompt_template = """
You are a Python expert skilled in using the pandas library to manipulate data! Your task is to generate Python code that performs operations on datasets based on their column names. The datasets are loaded into pandas DataFrames from Excel files with multiple sheets or CSV files.

The column names from the Excel sheets or CSV files are as follows:
"""

for sheet, cols in column_names.items():
    prompt_template += f"\nSheet '{sheet}' has columns: {', '.join(cols)} (File type: {file_types[sheet]})"

prompt_template += "\nThe files are stored at the following paths:"
for file_path in file_paths:
    prompt_template += f"\n- {file_path}"

prompt_template += "\n\nPlease generate the Python code based on the following user question and the datasets provided:\n"

# Submit button
submit = st.button("Submit")

if submit and dfs:
    full_prompt = prompt_template + question
    response = get_gemini_response(question, full_prompt)
    cleaned_code = clean_generated_code(response)
    
    st.subheader("The cleaned generated query is given below ")
    st.code(cleaned_code)

    try:
        local_namespace = {'pd': pd, 'plt': plt}
        with StringIO() as buf, redirect_stdout(buf):
            exec(cleaned_code, local_namespace)
            output = buf.getvalue()

        if 'plt' in local_namespace and callable(getattr(plt, 'get_fignums', None)) and plt.get_fignums():
            st.pyplot(plt)
        else:
            st.text(output.strip())

    except Exception as e:
        st.error(f"An error occurred while executing the cleaned generated code: {e}")

    st.session_state.messages.append({"role": "user", "content": question})
    st.session_state.messages.append({"role": "response_dataframe_query", "content": cleaned_code})
