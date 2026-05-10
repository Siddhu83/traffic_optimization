# traffic_optimization

## Live Junction Simulation Dashboard

Run the Streamlit dashboard locally:

```powershell
cd c:\Users\Gnanendra\Downloads\traffic_optimization
.\.venv\Scripts\python.exe -m streamlit run src/dashboard.py
```

The dashboard reads from `data/traffic_state.json` and `data/signal_commands.json`. If these files are not present, it falls back to demo mode and generates synthetic traffic automatically.
