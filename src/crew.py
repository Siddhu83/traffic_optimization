import json
from pathlib import Path
import yaml

# Import the traffic optimization logic
from logic.optimizer import optimize, get_optimizer, TrafficOptimizer


class TrafficCrew():
    """Traffic Optimization Crew - Simplified for reliability"""

    def __init__(self):
        # Initialize traffic optimizer
        self.optimizer = get_optimizer()
        
        # Load config files
        config_dir = Path(__file__).parent / "config"
        with open(config_dir / "agents.yaml", "r") as f:
            self.agents_config = yaml.safe_load(f)
        with open(config_dir / "tasks.yaml", "r") as f:
            self.tasks_config = yaml.safe_load(f)

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

    def crew(self):
        """
        Backwards-compatible adapter for older scripts that used CrewAI's
        generated .crew().kickoff(...) entrypoint.
        """
        return self

    def kickoff(self, inputs=None):
        """
        Simplified kickoff that uses the optimizer directly instead of CrewAI agents.
        This ensures reliable execution without LLM dependency issues.
        """
        try:
            traffic_data = inputs.get("traffic_data") if inputs else {}
            
            if isinstance(traffic_data, str):
                traffic_data = json.loads(traffic_data)
            
            # Analyze: Identify most congested lane
            print(f"[Traffic Analyzer] Analyzing traffic: {traffic_data}")
            
            # Optimize: Generate signal command
            signal_command = self.optimize_signal_timing(traffic_data)
            print(f"[Signal Strategist] Optimized command: {signal_command}")
            
            if not signal_command.get("reason"):
                signal_command["reason"] = (
                    f"Adaptive optimization for lanes N={traffic_data.get('N', 0)}, "
                    f"S={traffic_data.get('S', 0)}, E={traffic_data.get('E', 0)}, "
                    f"W={traffic_data.get('W', 0)}"
                )
            
            # Save result
            output_file = Path(__file__).parent.parent / "data" / "signal_commands.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w") as f:
                json.dump(signal_command, f, indent=2)
            
            class Result:
                def __init__(self, data):
                    self.raw = json.dumps(data)
            
            return Result(signal_command)
            
        except Exception as e:
            print(f"[Crew Error] {e}")
            raise
