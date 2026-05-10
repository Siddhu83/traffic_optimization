# 🚦 AI Traffic Junction Optimizer

An intelligent, multi-agent traffic junction optimization system built with CrewAI, YOLOv8, and Streamlit. The system uses a real-time vision model to assess traffic load and a crew of AI agents to optimize signal timing based on conditions like emergency vehicle presence and overall traffic volume.

## 🏗️ System Architecture

The project is divided into three main decoupled components:
1. **Vision Module (`src/vision/traffic_vision.py`)**: A YOLOv8-based script that processes a video feed, identifies vehicles, sorts them into N/S/E/W lanes, flags emergencies, and writes the snapshot to `data/traffic_state.json` and `data/vision_output.jpg`.
2. **AI Logic Engine (`src/main.py` & `src/crew.py`)**: A continuous heartbeat process that listens for new `traffic_state.json` updates. Upon receiving new data, it delegates the decision-making to a CrewAI setup (using Gemini and Llama 3) to pick the optimal traffic signal. It saves decisions to `data/signal_commands.json` and outputs thoughts to `data/agent_logs.json`.
3. **Dashboard (`dashboard/app.py`)**: A modern, dark-themed Streamlit web app that provides a digital twin of the intersection, live KPI updates, and transparency into the AI agents' reasoning process.

## 🚀 Execution Steps

### Prerequisites
Make sure your Python virtual environment or Docker container is active and dependencies are installed. (If you're using the provided DevContainer, this is handled automatically).
```bash
pip install -r requirements.txt
```

Verify your `.env` file exists and has the correct keys:
```env
GEMINI_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
```

### Running the Full System
To run the full end-to-end system, you will need to open **three separate terminal windows** and run one component in each.

#### Terminal 1: The UI Dashboard
Launch the Streamlit web dashboard. It will automatically listen for updates in the `data/` directory.
```bash
streamlit run dashboard/app.py
```
> The dashboard will open in your browser at `http://localhost:8501`.

#### Terminal 2: The Agent Logic Heartbeat
Start the main orchestration process. This script waits for new data from the vision module and kicks off the AI agents.
```bash
python src/main.py
```
> You will see a "heartbeat" message waiting for new data.

#### Terminal 3: The Vision Script (or Mock Generator)
**Option A: Mock Data Generator (Easiest)**
If you don't have a video handy or just want to test the UI and logic loop rapidly, run the mock data script:
```bash
python mock_data_generator.py
```

**Option B: Real Video Feed**
Run the YOLOv8 vision script and pass it a video file (or `0` for webcam). It will analyze frames and trigger the logic loop.
```bash
python src/vision/traffic_vision.py --source path/to/your/video.mp4
```

## 📂 Directory Structure
- `src/main.py`: The entrypoint for the AI logic heartbeat.
- `src/crew.py`: The CrewAI orchestration defining the agents and tasks.
- `src/vision/`: The YOLOv8 computer vision logic.
- `src/logic/`: The mathematical baseline traffic optimization formulas.
- `dashboard/`: The Streamlit web interface.
- `data/`: The shared directory acting as the pipeline buffer (JSON states and images).