from crewai import Agent, Task, Crew
from crewai_tools import (
    FileReadTool,
    WebsiteSearchTool,
)
from crewai_tools import tools
from langchain_groq import ChatGroq
from secret import GROQ_APIKEY, GEMINI_APIKEY
import os
import tools 
import utils
import streamlit as st
import gradio as gr
import shutil
import tempfile

# Create a temporary directory to store uploaded files
DATAROOM_PATH = tempfile.mkdtemp()
print(f"Temporary upload directory: {DATAROOM_PATH}")

def start_crew():
    llm = utils.gen_llm(GEMINI_APIKEY)

    agent = Agent(
        role="You are an investment analyst at a Venture Capital firm. Your job is to research and write screening memos for different VC funds.",
        goal="Complete any task given to you as effectivley as possible. Note, not everything will be provided in the dataroom. If this is the case, try to answer frmo your own training data. If any of your tools produce an error as an output, do not retry that actions with the same input. They will produce the same error output and it will be a waste of resorurces.",
        backstory=f"You are an extremely intelegent and hard worker. You also have access ot a dataroom. Here are some files in data dataroom: f{os.listdir('./dataroom')}",
        llm=llm,
        verbose=True,
        rate_limit=5,
        tools=[ 
            tools.create_dataroom_tool(DATAROOM_PATH)(),
        ],
    )

    task = Task (
        description="Do a write up about ASML's financials and moat.",
        expected_output="ASML is a lithography comany ...",
        agent=agent,
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=2,
    )

    result = crew.kickoff()
    print(result)

def process_files(files):
    """
    Process uploaded files and return a file for download.
    """
    # Save uploaded files
    saved_paths = []
    for file in files:
        file_path = os.path.join(DATAROOM_PATH, file.name)
        try:
            shutil.copyfile(file.name, file_path)
        except shutil.SameFileError:
            pass
        saved_paths.append(file_path)
    
    print(f"Saved {len(saved_paths)} files.")
    if os.path.exists("output.docx"):
        os.remove("output.docx")
    shutil.copyfile("./templates/TEMPLATE FUND Screening Memo.docx", "output.docx")

    start_crew()

    return 'output.docx'

# Define the Gradio interface
with gr.Blocks() as demo:
    gr.Markdown("# File Processor")
    
    with gr.Row():
        input_files = gr.File(label="Upload your files", file_count="multiple")
        output_file = gr.File(label="Processed file")
    
    process_btn = gr.Button("Process Files")
    process_btn.click(fn=process_files, inputs=input_files, outputs=output_file)

    gr.Markdown("""
    ## Instructions
    1. Upload one or more files using the file uploader.
    2. Click the "Process Files" button.
    3. The processed file will appear in the output section, ready for download.
    """)

# Launch the app
if __name__ == "__main__":
    # Cleanup function to remove temporary directory when the script exits
    def cleanup():
        print(f"Cleaning up temporary directory: {DATAROOM_PATH}")
        shutil.rmtree(DATAROOM_PATH)

    # Register the cleanup function
    import atexit
    atexit.register(cleanup)

    # Launch the Gradio interface
    demo.launch()

