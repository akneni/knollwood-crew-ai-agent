import sys

# Handle cli arguments and display help message before importing
# all other dependencies (as this takes a while)
cli_arg = '--gui' if len(sys.argv) < 2 else sys.argv[1]
if cli_arg not in ['--gui', '--cli']:
    with open('./docs/cli-usage.md', 'r') as f:
        text = f.read()
        print(text)
        exit()


from crewai import Agent, Task, Crew, Process
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
from pprint import pprint
import atexit
import constants
from agent_int import KwiAgent, KwiTask


def start_crew(fund_name):
    # llm = utils.gen_llm(GROQ_APIKEY, model="Mixtral-8x7b-32768")
    llm = utils.gen_llm(GEMINI_APIKEY)

    kwi_agent_set: list[KwiAgent] = KwiAgent.from_json('./templates/agent-templates.json', fund_name)
    kwi_task_set: list[KwiTask] = KwiTask.from_json('./templates/task-templates.json')

    # Ensure that all tags are assigned to one agent
    tags = KwiAgent.extract_tags(kwi_agent_set)
    if len((diff := (set(i.section for i in kwi_task_set)) - set(tags))):
        print(f"WARNING -> UNASSIGNED TAGS:")
        pprint(diff)
        exit(0)

    task_set = []
    agent_set = []
    for t in kwi_task_set:
        a = t.select_agent(kwi_agent_set)
        agent_set.append(a.get_writer(llm))
        task_set.append(Task(
            **t.into_writer(),
            agent=agent_set[-1],
        ))
        agent_set.append(a.get_researcher(llm))
        task_set.append(Task(
            **t.into_researcher(),
            agent=agent_set[-1],
        ))

    crew = Crew(
        agents=agent_set,
        tasks=task_set,
        verbose=True,
        # process=Process.hierarchical,
        # manager_llm=llm,
    )

    result = crew.kickoff()
    print(result)

    utils.build_word_doc("./outputs", fund_name)
    return os.path.join("./outputs", "screening-memo.docx")

def handle_gradio(files, fund_name):
    """
    Process uploaded files and return a file for download.
    """
    # Save uploaded files
    saved_paths = []
    for file in files:
        file_path = os.path.join("./dataroom", file.name)
        try:
            shutil.copyfile(file.name, file_path)
        except shutil.SameFileError:
            pass
        saved_paths.append(file_path)
    
    print(f"Saved {len(saved_paths)} files.")

    out_path = start_crew(fund_name)

    return out_path

def read_logs():
    with open("output-file.log", "r") as f:
        return f.read()

# Define the Gradio interface favicon="./icon/knollwood-icon.jpeg"
with gr.Blocks(title="Knollwood Internal") as demo:
    gr.Markdown("# Funds Screening Memo Writer")    

    fund_name = gr.Text("Fund Name: ")
    with gr.Row():
        input_files = gr.File(label="Upload your files", file_count="multiple")
        output_file = gr.File(label="Processed file")
    
    process_btn = gr.Button("Run AI Crew")
    process_btn.click(fn=handle_gradio, inputs=[input_files, fund_name], outputs=output_file)

    gr.Markdown("""
    ## Instructions
    1. Upload one or more files using the file uploader.
    2. Click the "Run AI Crew" button.
    3. The screening memo will appear in the output section, ready for download.
    """)

    logs = gr.Textbox(label="Model Thoughts")
    demo.load(read_logs, None, logs, every=1)



# Cleanup function to remove temporary directory when the script exits
def cleanup():
    for filepath in os.listdir('./dataroom'):
        filepath = os.path.join('./dataroom', filepath)
        if os.path.isfile(filepath):
            os.remove(filepath)
        elif os.path.isdir(filepath):
            shutil.rmtree(filepath)

# Launch the app
if __name__ == "__main__":
    shelve_path = "./outputs/shelve-db"
    if os.path.exists(shelve_path):
        shutil.rmtree(shelve_path)
    if not os.path.exists(shelve_path):
        os.mkdir(shelve_path)

    # Handle gui
    if cli_arg == '--gui':
        atexit.register(cleanup)
        demo.launch()

    # Handle CLI
    elif cli_arg == '--cli':
        dataroom_dir = input("Enter the path to your dataroom: ")
        fund_name = input("Enter the fund name: ")

        for path in os.listdir(dataroom_dir):
            src = os.path.join(dataroom_dir, path)
            dst = os.path.join("./dataroom", path)
            try:
                if os.path.isfile(src):
                    shutil.copyfile(src, dst)
                elif os.path.isdir(src):
                    shutil.copytree(src, dst)
            except shutil.SameFileError:
                pass

        start_crew(fund_name)
