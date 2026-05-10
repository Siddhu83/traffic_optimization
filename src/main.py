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
    
    while True:
        try:
            if traffic_state_file.exists():
                print(f"[{time.strftime('%X')}] 📈 Found traffic_state.json. Triggering TrafficCrew...")
                
                # Load the input data from the Vision module
                try:
                    with open(traffic_state_file, "r") as f:
                        inputs = json.load(f)
                except json.JSONDecodeError:
                    print(f"[{time.strftime('%X')}] ⚠️  Error reading JSON. Waiting for Vision to finish writing...")
                    time.sleep(2)
                    continue

                print(f"Inputs: {inputs}")
                
                # Create traffic crew and execute optimization
                traffic_crew = TrafficCrew()
                result = traffic_crew.kickoff(inputs={"traffic_data": json.dumps(inputs)})
                
                print(f"[{time.strftime('%X')}] ✅ Crew finished.")
                print(f"Result saved to data/signal_commands.json: {result.raw}")
                
                # We rename or delete the file so we don't process it endlessly
                # Remove it so the system waits for the Vision module to create the next snapshot
                traffic_state_file.unlink()
                print(f"[{time.strftime('%X')}] 🗑️  Cleaned up traffic_state.json. Waiting for next snapshot...")
            else:
                pass # Silent heartbeat, waiting for data
                
        except Exception as e:
            print(f"[{time.strftime('%X')}] ❌ Error in heartbeat loop: {e}")
            
        time.sleep(5)

if __name__ == "__main__":
    main()
