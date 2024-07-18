import sys

# Handle cli arguments and display help message before importing
# all other dependencies (as this takes a while)
cli_arg = '--gui' if len(sys.argv) < 2 else sys.argv[1]
if cli_arg not in ['--gui', '--cli']:
    with open('./docs/cli-usage.md', 'r') as f:
        text = f.read()
        print(text)
        exit()


from crewai import Agent, Task, Crew
from crewai_tools import (
    FileReadTool,
    WebsiteSearchTool,
    DirectoryReadTool,
)
from crewai_tools import tools
from langchain_groq import ChatGroq
from secret import GROQ_APIKEY, GEMINI_APIKEY
import os
import tools 
import utils
import agents
import gradio as gr
import shutil
import tempfile
import atexit
import constants

# Create a temporary directory to store uploaded files

WORKING_DIR = tempfile.mkdtemp()
OUTPUTS_PATH = os.path.join(WORKING_DIR, "outputs")
OUTPUTS_PATH = "./outputs"

# DATAROOM_PATH = os.path.join(WORKING_DIR, "./dataroom") if cli_arg == '--gui' else input("Enter the filepath to your dataroom: ")
DATAROOM_PATH = os.path.join(WORKING_DIR, "dataroom") if cli_arg == '--gui' else "/home/aknen/MEGA/Knollwood/Projects/crew-ai/dataroom/"
# Create sub directories
for path in [DATAROOM_PATH, OUTPUTS_PATH]:
    if not os.path.exists(path):
        os.mkdir(path)

print(f"Reading dataroom from: {DATAROOM_PATH}")

def start_crew():
    # llm = utils.gen_llm(GROQ_APIKEY, model="Mixtral-8x7b-32768")
    llm = utils.gen_llm(GEMINI_APIKEY)

    agent_set = []
    tasks = []

    for section, agent_pair in agents.create_crew(llm, 'CyberStarts Opportunity Fund', DATAROOM_PATH, OUTPUTS_PATH, constants.SECTIONS):
        r_task = Task (
            description=f"Gather data about the {section} section from the data room or your own training data.",
            expected_output=f"Your output should be notes in markdown about the {section} section.",
            agent=agent_pair['researcher'],
        )

        w_task = Task (
            description=f"Using the data that your researcher gathered, fill in the {section} section of the screening memo.",
            expected_output=f"Your output should be information about your section that would be helpful for making an investment decision.",
            agent=agent_pair['writer'],
        )
        tasks.append(r_task)
        tasks.append(w_task)
        agent_set.append(agent_pair['researcher'])
        agent_set.append(agent_pair['writer'])

    crew = Crew(
        agents=agent_set,
        tasks=tasks,
        verbose=2,
    )

    result = crew.kickoff()
    print(result)

    utils.build_word_doc(OUTPUTS_PATH)
    return os.path.join(OUTPUTS_PATH, "screening-memo.docx")

def handle_gradio(files):
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

    out_path = start_crew()

    return out_path

# Define the Gradio interface favicon="./icon/knollwood-icon.jpeg"
with gr.Blocks(title="Knollwood Internal") as demo:
    gr.Markdown("# Funds Screening Memo Writer")    

    with gr.Row():
        input_files = gr.File(label="Upload your files", file_count="multiple")
        output_file = gr.File(label="Processed file")
    
    process_btn = gr.Button("Run AI Crew")
    process_btn.click(fn=handle_gradio, inputs=input_files, outputs=output_file)

    gr.Markdown("""
    ## Instructions
    1. Upload one or more files using the file uploader.
    2. Click the "Run AI Crew" button.
    3. The screening memo will appear in the output section, ready for download.
    """)

# Cleanup function to remove temporary directory when the script exits
def cleanup():
    print(f"Cleaning up temporary directory: {DATAROOM_PATH}")
    shutil.rmtree(DATAROOM_PATH)

# Launch the app
if __name__ == "__main__":
    shelve_path = os.path.join(OUTPUTS_PATH, "shelve-db")
    if os.path.exists(shelve_path):
        shutil.rmtree(shelve_path)
    os.mkdir(shelve_path)

    # Handle gui
    if cli_arg == '--gui':
        atexit.register(cleanup)
        demo.launch()

    # Handle CLI
    elif cli_arg == '--cli':
        start_crew()
