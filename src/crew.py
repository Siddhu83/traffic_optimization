import os
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

@CrewBase
class TrafficCrew():
    """Traffic Optimization Crew"""

    # These paths are relative to the directory where this script resides (src/)
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self):
        # Gemini 2.5 Flash for high context and reasoning (Traffic Data Scientist)
        self.gemini_llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            api_key=os.environ.get("GEMINI_API_KEY")
        )
        
        # Groq (Llama 3) for high speed real-time strategy (Senior Traffic Engineer)
        self.groq_llm = ChatGroq(
            model="llama-3.3-70b-versatile", # You can adjust this to the exact Llama 3 model string supported by Groq
            groq_api_key=os.environ.get("GROQ_API_KEY")
        )

    @agent
    def traffic_analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config['traffic_analyzer'],
            llm=self.gemini_llm,
            verbose=True
        )

    @agent
    def signal_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config['signal_strategist'],
            llm=self.groq_llm,
            verbose=True
        )

    @task
    def analyze_traffic_task(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_traffic_task']
        )

    @task
    def optimize_signals_task(self) -> Task:
        return Task(
            config=self.tasks_config['optimize_signals_task'],
            output_file='data/signal_commands.json'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the TrafficCrew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
