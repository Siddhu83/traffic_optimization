import os
import json
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

# Import the traffic optimization logic
from logic.optimizer import optimize, get_optimizer, TrafficOptimizer

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

        # Initialize traffic optimizer
        self.optimizer = get_optimizer()

    def optimize_signal_timing(self, traffic_data) -> dict:
        """
        Tool: Optimize signal timing based on current traffic state.
        
        Args:
            traffic_data: Dictionary or JSON string with N, S, E, W vehicle counts and emergency flag
                Example: {'N': 10, 'S': 5, 'E': 8, 'W': 12, 'emergency': False}
        
        Returns:
            Dictionary with optimal signal command containing:
            - lane: The direction to give green light (N, S, E, W)
            - seconds: Duration of green light
            - priority: Boolean for emergency priority mode
            - reason: Explanation of the decision
        """
        if isinstance(traffic_data, str):
            try:
                import json
                traffic_data = json.loads(traffic_data.replace("'", '"'))
            except Exception:
                pass
        return optimize(traffic_data)
    
    def get_optimizer_stats(self) -> dict:
        """
        Tool: Get cumulative optimizer statistics for reporting.
        
        Returns:
            Dictionary with impact metrics:
            - total_vehicles_processed
            - total_time_saved_seconds
            - co2_saved_grams
            - co2_saved_kg
        """
        return self.optimizer.get_impact_stats()
    
    def reset_optimizer_stats(self) -> dict:
        """
        Tool: Reset optimizer statistics (useful for new simulation runs).
        
        Returns:
            Confirmation message
        """
        self.optimizer.reset_stats()
        return {"status": "success", "message": "Optimizer statistics reset"}

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
            verbose=True,
            tools=[self.optimize_signal_timing]  # Register optimizer as tool
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
