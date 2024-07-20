from crewai import Agent
import tools
import os
import json
import functools

@functools.cache
def fetch_template(agent_type: str):
    if agent_type not in ['researcher', 'writer']:
        raise ValueError(f"argument `agent_type` must be one of ['writer', 'researcher'], received: {agent_type}")
    with open('./templates/agent-templates.json', 'r') as f:
        prompts = json.load(f)
    return prompts[agent_type]

def create_agent(
    llm, 
    fund_name: str,
    dataroom_path: str, 
    output_path: str, 
    agent_section: str,
    agent_type: str
):
    if agent_type not in ['writer', 'researcher']:
        raise ValueError(f"argument `agent_type` must be one of ['writer', 'researcher'], received: {agent_type}")
    
    # get prompt for the agent's role
    prompt_template = {
        k:v.replace('<[Section Name]>', agent_section).replace('<[Fund Name]>', fund_name)
        for k, v in fetch_template(agent_type).items()
    }

    # Check if any tags are missing
    if any('<[' in v for v in prompt_template.values()):
        unreplaced_lines = [v for v in prompt_template.values() if '<[' in v]
        raise Exception(f"All of the tags in the prompt template have not been replaced:\n{unreplaced_lines}")

    # Equip the necessary tools for the agent's functions
    if agent_type == 'researcher':
        agent_tools = [tools.gen_qd(dataroom_path)()]
    else:
        agent_tools = [ 
            tools.add_to_screening_memo,
            tools.read_screening_memo,
        ]

    agent = Agent(
        role=prompt_template['role'],
        goal=prompt_template['goal'],
        backstory=prompt_template['backstory'],
        llm=llm,
        verbose=True,
        rate_limit= 8 if agent_type=='researcher' else 6,
        tools=agent_tools,
        output_file=output_path,
    )
    return agent

def create_crew(llm, fund_name: str, dataroom_path: str, output_path: str, sections: list[str]) -> dict:
    agent_dict = {}
    
    for section in sections:
        section = section.strip("<[]>")
        researcher = create_agent(llm, fund_name, dataroom_path, output_path, section, 'researcher')
        writer = create_agent(llm, fund_name, dataroom_path, output_path, section, 'writer')
        agent_dict[section] = {
            'researcher': researcher,
            'writer': writer,
        }
    
    return agent_dict

