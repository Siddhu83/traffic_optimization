import json
import time
import random
import os
import shutil

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def generate_mock_data():
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Generate mock image if it doesn't exist
    img_path = os.path.join(DATA_DIR, "vision_output.jpg")
    if not os.path.exists(img_path):
        try:
            from PIL import Image, ImageDraw
            img = Image.new('RGB', (800, 600), color=(40, 40, 40))
            d = ImageDraw.Draw(img)
            d.text((350, 280), "Mock Vision Output", fill=(255, 255, 255))
            img.save(img_path)
        except ImportError:
            print("PIL not installed. Creating a dummy file.")
            with open(img_path, "wb") as f:
                f.write(b"")

    print(f"Generating mock data in {DATA_DIR}. Press Ctrl+C to stop.")

    while True:
        try:
            # Mock traffic state
            traffic_state = {
                "N": random.randint(0, 30),
                "S": random.randint(0, 30),
                "E": random.randint(0, 30),
                "W": random.randint(0, 30),
                "emergency": random.random() < 0.1  # 10% chance of emergency
            }
            
            with open(os.path.join(DATA_DIR, "traffic_state.json"), "w") as f:
                json.dump(traffic_state, f, indent=4)
                
            # Mock signal commands
            directions = ["N", "S", "E", "W"]
            green_dir = random.choice(directions)
            
            signal_commands = {
                "N": "GREEN" if green_dir == "N" else "RED",
                "S": "GREEN" if green_dir == "S" else "RED",
                "E": "GREEN" if green_dir == "E" else "RED",
                "W": "GREEN" if green_dir == "W" else "RED",
            }
            
            with open(os.path.join(DATA_DIR, "signal_commands.json"), "w") as f:
                json.dump(signal_commands, f, indent=4)
                
            # Mock agent logs
            agent_logs = [
                {"agent": "Vision Specialist", "message": f"Detected traffic load - N:{traffic_state['N']}, S:{traffic_state['S']}, E:{traffic_state['E']}, W:{traffic_state['W']}"},
                {"agent": "Architect", "message": f"Analyzing intersection state. Emergency status: {traffic_state['emergency']}"},
                {"agent": "Signal Optimizer", "message": f"Prioritizing direction {green_dir}. Changing lights."}
            ]
            
            with open(os.path.join(DATA_DIR, "agent_logs.json"), "w") as f:
                json.dump(agent_logs, f, indent=4)

            time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping mock data generation.")
            break
        except Exception as e:
            print(f"Error generating data: {e}")
            time.sleep(1)

if __name__ == "__main__":
    generate_mock_data()
