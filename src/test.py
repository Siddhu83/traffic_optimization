import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import json
from crew import TrafficCrew

def main():
    dummy_data = {
        "N": 10,
        "S": 2,
        "E": 5,
        "W": 22,
        "emergency": False
    }

    print("Kicking off crew with dummy data...")
    print(dummy_data)
    
    crew = TrafficCrew().crew()
    result = crew.kickoff(inputs={"traffic_data": json.dumps(dummy_data)})
    
    print("\n\n==== DONE ====")
    print("Result JSON:", result.raw)

if __name__ == "__main__":
    main()
