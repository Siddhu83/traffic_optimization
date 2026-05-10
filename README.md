# AI Based Junction Optimization System

Demo-ready prototype for smart traffic signal control at a four-way junction.

## What It Shows

- Vehicle counting from a camera or video using YOLOv8.
- Adaptive green-light timing based on lane density.
- Emergency vehicle priority mode.
- Fairness handling for empty/deadlock and starvation scenarios.
- Live Streamlit dashboard with synthetic demo mode when no camera feed is running.
- JSON handoff between the vision module, optimizer, and dashboard.

## Quick Demo

Run the dashboard. It starts in synthetic demo mode automatically:

```powershell
cd c:\Users\Gnanendra\Downloads\traffic_optimization
.\.venv\Scripts\python.exe -m streamlit run src/dashboard.py
```

The dashboard reads:

- `data/traffic_state.json` for live lane counts from the vision module.
- `data/signal_commands.json` for optimized signal commands.

If `traffic_state.json` is missing, the dashboard generates realistic demo traffic and still uses the real optimizer.

## Optional Live Vision Feed

In a second terminal, run YOLO detection from a webcam:

```powershell
cd c:\Users\Gnanendra\Downloads\traffic_optimization
.\.venv\Scripts\python.exe src/vision/traffic_vision.py --source 0
```

Or use a video file:

```powershell
.\.venv\Scripts\python.exe src/vision/traffic_vision.py --source demo.mp4
```

Then run the optimizer heartbeat in another terminal:

```powershell
.\.venv\Scripts\python.exe src/main.py
```

## Verify Before Presenting

```powershell
cd c:\Users\Gnanendra\Downloads\traffic_optimization
.\.venv\Scripts\python.exe src/logic/test_optimizer.py
.\.venv\Scripts\python.exe src/logic/test_integration.py
.\.venv\Scripts\python.exe src/test.py
```

Expected result: all optimizer and integration checks pass, and `src/test.py` writes a signal command to `data/signal_commands.json`.

## Notes

Emergency detection in the demo treats buses/trucks in the priority ROI as priority vehicles. For a production system, train or fine-tune a model with an ambulance/emergency-vehicle class.
