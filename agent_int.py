import tools
import json
from crewai import Agent

class KwiAgent:
    def __init__(self) -> None:
        self.writer = {
            'role': '',
            'goal': '',
            'backstory': '',
        }
        self.researcher = {
            'role': '',
            'goal': '',
            'backstory': '',
        }
        self.sections: list[str] = []
    
    def get_researcher(self, llm) -> Agent:
        return Agent (
            role=self.researcher['role'],
            goal=self.researcher['goal'],
            backstory=self.researcher['backstory'],
            llm=llm,
            verbose=True,
            rate_limit= 8,
            tools = [tools.gen_qd("./dataroom")()],
        )

    def get_writer(self, llm) -> Agent:
        return Agent (
            role=self.writer['role'],
            goal=self.writer['goal'],
            backstory=self.writer['backstory'],
            llm=llm,
            verbose=True,
            rate_limit= 6,
            tools = [
                tools.add_to_screening_memo,
                tools.read_screening_memo,
            ],
        )
    
    def attach_fund_name(self, name: str):
        self.writer = {
            k:v.replace("<[Fund Name]>", name) 
            for k, v in self.writer.items()
        }
        self.researcher = {
            k:v.replace("<[Fund Name]>", name) 
            for k, v in self.researcher.items()
        }

    @staticmethod
    def from_json(path, fund_name: str = None) -> list:
        with open(path, 'r') as f:
            data = json.load(f)

        if fund_name is not None:
            data['writer'] = {
                k:v.replace("<[Fund Name]>", fund_name) 
                for k, v in data['writer'].items()
            }
            data['researcher'] = {
                k:v.replace("<[Fund Name]>", fund_name) 
                for k, v in data['researcher'].items()
            }

        agents = []
        for section in data['sections']:
            ph = KwiAgent()
            ph.sections = section
            ph.writer = {
                k:v.replace("<[Section Name]>", str(ph.sections)) 
                for k, v in data['writer'].items()
            }
            ph.researcher = {
                k:v.replace("<[Section Name]>", str(ph.sections)) 
                for k, v in data['researcher'].items()
            }

            if len(err_tags := [i for i in ph.sections if not (i.startswith('<[') and i.endswith(']>'))]) > 0:
                raise Exception(f"Incorrect tag formatting:\n{err_tags}")
            
            agents.append(ph)

        return agents

    @staticmethod
    def extract_tags(lst) -> list[str]:
        res = []
        for agent in lst:
            res += agent.sections
        return res

    def __str__(self) -> str:
        return f"KwiAgent(tags={self.sections})"
    
    def __repr__(self) -> str:
        return str(self)

class KwiTask:
    def __init__(self, section, special_instructions, expected_output) -> None:
        self.section = section
        self.special_instructions = special_instructions.replace('<[Section]>', section[2:-2])
        self.expected_output = expected_output.replace('<[Section]>', section[2:-2])
    
    
    def into_writer(self) -> dict:
        writer_prompt = f'Your job is to fill in the {self.section} section in this screeneing memo using plain text (not markdown or any other format). Here are some additional instructions for this section:'
        return {
            'description': f'{writer_prompt} {self.special_instructions}',
            'expected_output': self.expected_output,
        }
    
    def into_researcher(self) -> dict:
        writer_prompt = f'Your job is to research data for the section. {self.section}'
        return {
            'description': f'{writer_prompt} {self.special_instructions}',
            'expected_output': 'You notes should ideally be in markdown',
        }
    
    def select_agent(self, agents: list[KwiAgent]) -> KwiAgent:
        for agent in agents:
            if self.section in agent.sections:
                return agent
        raise Exception(f"Tag {self.section} does not exist in any agent")

    @staticmethod
    def from_json(path) -> list:
        with open(path, 'r') as f:
            data = json.load(f)
        tasks = []
        for i in data:
            tasks.append(KwiTask(**i))
        return tasks
    
    def __str__(self) -> str:
        return f"Task(section{self.section})"
    
    def __repr__(self) -> str:
        return str(self)