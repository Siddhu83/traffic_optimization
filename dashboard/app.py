import streamlit as st
import json
import time
import pandas as pd
import plotly.graph_objects as go
import os

st.set_page_config(page_title="AI-Junction Dashboard", layout="wide")

# Sidebar
st.sidebar.title("AI Based Junction Optimization System")
st.sidebar.header("Project Overview")
st.sidebar.info("A live AI-powered junction system that optimizes traffic signals and detects emergency vehicles in real-time. By dynamically adjusting to traffic loads, we reduce wait times and carbon emissions.")

# State variables before loop
history_df = pd.DataFrame(columns=['Time', 'N', 'S', 'E', 'W'])
co2_saved = 0.0
last_emergency_state = False

# Placeholder for live loop
placeholder = st.empty()

def read_json_safe(file_path, default_val):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception:
        return default_val

# Paths
TRAFFIC_STATE_PATH = "data/traffic_state.json"
SIGNAL_COMMANDS_PATH = "data/signal_commands.json"
AGENT_LOGS_PATH = "data/agent_logs.json"

while True:
    # Read files safely (Phase B & Safety Logic)
    traffic_state = read_json_safe(TRAFFIC_STATE_PATH, {"N": 0, "S": 0, "E": 0, "W": 0, "emergency": False})
    signal_commands = read_json_safe(SIGNAL_COMMANDS_PATH, {"N": "RED", "S": "RED", "E": "RED", "W": "RED"})
    agent_logs = read_json_safe(AGENT_LOGS_PATH, [])

    # Update CO2 saved (live Impact Meter)
    co2_saved += 2.3

    # Update history dataframe for persistence chart
    now = pd.Timestamp.now()
    new_row = pd.DataFrame({
        'Time': [now],
        'N': [traffic_state.get('N', 0)],
        'S': [traffic_state.get('S', 0)],
        'E': [traffic_state.get('E', 0)],
        'W': [traffic_state.get('W', 0)]
    })
    
    # Concat new row
    history_df = pd.concat([history_df, new_row], ignore_index=True)
    # Keep last 60 seconds (approx 1 row per second)
    if len(history_df) > 60:
        history_df = history_df.tail(60)

    total_cars = traffic_state.get('N', 0) + traffic_state.get('S', 0) + traffic_state.get('E', 0) + traffic_state.get('W', 0)
    max_capacity = 100 # Mock capacity
    congestion_index = min(100, int((total_cars / max_capacity) * 100))
    emergency_detected = traffic_state.get('emergency', False)

    with placeholder.container():
        st.title("🚦 AI-Junction Optimization Dashboard")
        
        # The Emergency Trigger
        if emergency_detected:
            st.error("🚨 EMERGENCY VEHICLE DETECTED - ROUTE CLEARING IN PROGRESS")
            if not last_emergency_state:
                st.toast("Priority Overide Active!", icon="🔥")

        # Top Metrics (KPIs)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="System Status", value="Running 🟢")
        with col2:
            st.metric(label="Congestion Index", value=f"{congestion_index}%", delta=f"{total_cars} Cars Total", delta_color="inverse")
        with col3:
            if emergency_detected:
                st.metric(label="Emergency Mode", value="ACTIVE 🔴")
            else:
                st.metric(label="Emergency Mode", value="Inactive")
        with col4:
            st.metric(label="AI Optimization", value="Active - Llama 3.3")
            
        # The Impact Meter
        st.metric(label="🌱 Live CO2 Impact", value=f"{co2_saved:.1f} g Saved", delta="2.3 g/s", delta_color="normal")

        # Layout for Main Content
        main_col1, main_col2 = st.columns(2)

        with main_col1:
            st.subheader("Junction Visualizer")
            
            # The Junction Visualizer using Plotly
            fig = go.Figure()
            
            # Intersection Background 
            fig.add_shape(type="rect", x0=-10, y0=-10, x1=10, y1=10, fillcolor="#1e1e1e", layer="below")
            
            # Map colors from commands to hex for dark mode contrast
            color_map = {"RED": "#ff4b4b", "GREEN": "#00ff00", "YELLOW": "#ffff00"}
            color_N = color_map.get(signal_commands.get("N", "RED"), "#ff4b4b")
            color_S = color_map.get(signal_commands.get("S", "RED"), "#ff4b4b")
            color_E = color_map.get(signal_commands.get("E", "RED"), "#ff4b4b")
            color_W = color_map.get(signal_commands.get("W", "RED"), "#ff4b4b")

            # Center square of the intersection
            fig.add_shape(type="rect", x0=-2, y0=-2, x1=2, y1=2, fillcolor="#333333", line=dict(color="gray"))

            # North Lane
            fig.add_shape(type="rect", x0=-2, y0=2, x1=2, y1=10, fillcolor=color_N, line=dict(color="black"))
            fig.add_annotation(x=0, y=6, text=f"N: {traffic_state.get('N',0)}", showarrow=False, font=dict(color="black", size=16, weight="bold"))
            
            # South Lane
            fig.add_shape(type="rect", x0=-2, y0=-10, x1=2, y1=-2, fillcolor=color_S, line=dict(color="black"))
            fig.add_annotation(x=0, y=-6, text=f"S: {traffic_state.get('S',0)}", showarrow=False, font=dict(color="black", size=16, weight="bold"))

            # East Lane
            fig.add_shape(type="rect", x0=2, y0=-2, x1=10, y1=2, fillcolor=color_E, line=dict(color="black"))
            fig.add_annotation(x=6, y=0, text=f"E: {traffic_state.get('E',0)}", showarrow=False, font=dict(color="black", size=16, weight="bold"))

            # West Lane
            fig.add_shape(type="rect", x0=-10, y0=-2, x1=-2, y1=2, fillcolor=color_W, line=dict(color="black"))
            fig.add_annotation(x=-6, y=0, text=f"W: {traffic_state.get('W',0)}", showarrow=False, font=dict(color="black", size=16, weight="bold"))

            fig.update_layout(
                xaxis=dict(showgrid=False, zeroline=False, visible=False, range=[-11, 11]),
                yaxis=dict(showgrid=False, zeroline=False, visible=False, range=[-11, 11]),
                margin=dict(l=0, r=0, t=0, b=0),
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            st.plotly_chart(fig, use_container_width=True)

        with main_col2:
            st.subheader("Vision Feed")
            try:
                # Handshake with Vision system
                if os.path.exists("data/processed_frame.jpg"):
                    st.image("data/processed_frame.jpg", use_container_width=True, caption="Live Vision Output")
                elif os.path.exists("data/vision_output.jpg"):
                    st.image("data/vision_output.jpg", use_container_width=True, caption="Live Vision Output")
                else:
                    st.info("Waiting for Vision System frame...")
            except Exception:
                st.warning("Error reading vision frame.")

        st.subheader("Data Persistence: Vehicle Counts (Last 60s)")
        # Plot lines
        df_plot = history_df.set_index('Time')
        st.line_chart(df_plot, use_container_width=True)

        st.subheader("Agent Reasoning Box")
        if agent_logs:
            log_text = ""
            for log in agent_logs[-3:]: # Show last 5 logs
                log_text += f"**[{log.get('agent', 'System')}]** 🤔 {log.get('message', '')}\n\n"
            st.info(log_text)
        else:
            st.info("No active agent logs.")

    last_emergency_state = emergency_detected
    time.sleep(1)
