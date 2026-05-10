import time
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure we can import from src
sys.path.append(str(Path(__file__).parent))
from crew import TrafficCrew

# Load environment variables
load_dotenv()

def main():
    print("🚦 Starting Junction Optimization System heartbeat...")
    
    # Setup data directory
    workspace_root = Path(__file__).parent.parent
    data_dir = workspace_root / "data"
    data_dir.mkdir(exist_ok=True)
    
    traffic_state_file = data_dir / "traffic_state.json"
    
    last_mtime = 0
    while True:
        try:
            if traffic_state_file.exists():
                mtime = traffic_state_file.stat().st_mtime
                if mtime > last_mtime:
                    print(f"[{time.strftime('%X')}] 📈 Found new traffic_state.json. Triggering TrafficCrew...")
                    
                    # Load the input data from the Vision module
                    try:
                        with open(traffic_state_file, "r") as f:
                            inputs = json.load(f)
                    except json.JSONDecodeError:
                        print(f"[{time.strftime('%X')}] ⚠️  Error reading JSON. Waiting for Vision to finish writing...")
                        time.sleep(2)
                        continue

                    last_mtime = mtime
                    print(f"Inputs: {inputs}")
                    
                    # We inject the data read from JSON into the task description via inputs
                    crew = TrafficCrew().crew()
                    result = crew.kickoff(inputs={"traffic_data": json.dumps(inputs)})
                    
                    print(f"[{time.strftime('%X')}] ✅ Crew finished.")
                    print(f"Result saved to data/signal_commands.json: {result.raw}")
                    
                    # Write agent logs to data/agent_logs.json
                    try:
                        log_file = data_dir / "agent_logs.json"
                        reasoning = "Optimization complete based on current traffic."
                        try:
                            # Try to parse if it's JSON to get reasoning
                            res_json = json.loads(result.raw)
                            reasoning = res_json.get("reason", reasoning)
                        except:
                            pass
                        logs = [
                            {"agent": "Traffic Analyzer", "message": f"Analyzed traffic inputs: {inputs}"},
                            {"agent": "Signal Strategist", "message": f"Decision: {reasoning}"}
                        ]
                        with open(log_file, "w") as f:
                            json.dump(logs, f, indent=4)
                    except Exception as log_e:
                        print(f"[{time.strftime('%X')}] ⚠️  Error writing agent logs: {log_e}")
                else:
                    pass # Waiting for new data
            else:
                pass # Silent heartbeat, waiting for data
                
        except Exception as e:
            print(f"[{time.strftime('%X')}] ❌ Error in heartbeat loop: {e}")
            
        time.sleep(5)

if __name__ == "__main__":
    main()
