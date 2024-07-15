from crewai import Agent, Task, Crew
from langchain_groq import ChatGroq
from secret import GROQ_APIKEY
import os


os.environ.update({'GROQ_API_KEY': GROQ_APIKEY})

llm = ChatGroq(
    model="llama3-70b-4096",  # You can choose other models like "llama3-8b-8192"
    # api_key=GROQ_APIKEY
)

print(
    llm.invoke([
        ('system', 'You translate english to french.'),
        {'human', 'I like venture capital.'}
    ])
)

agent = Agent(
    role="You are a creative writer.",
    goal="Your goal is to excel in creative writing.",
    backstory="You graduated NYU for creative writing",
    llm=llm,
    verbose=True
)

task = Task (
    description="Write a short story about evil tooth faries.",
    expected_output='A bullet list summary of the top 5 most important AI news',
    agent=agent,
)


crew = Crew(
    agents=[agent],
    tasks=[task],
    verbose=2,
)

result = crew.kickoff()
print(result)