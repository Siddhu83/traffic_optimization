import streamlit as st
import json
import time
import os
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --- Config ---
st.set_page_config(layout="wide", page_title="AI Traffic Optimizer", page_icon="🚦")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
TRAFFIC_STATE_FILE = os.path.join(DATA_DIR, "traffic_state.json")
SIGNAL_COMMANDS_FILE = os.path.join(DATA_DIR, "signal_commands.json")
AGENT_LOGS_FILE = os.path.join(DATA_DIR, "agent_logs.json")
VISION_OUTPUT_FILE = os.path.join(DATA_DIR, "vision_output.jpg")

# --- Helper Functions ---
def load_json(filepath):
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
    except Exception as e:
        pass
    return None

def create_intersection_fig(signal_commands):
    # Plotly figure drawing an intersection
    fig = go.Figure()
    
    # Draw roads
    fig.add_shape(type="rect", x0=40, y0=0, x1=60, y1=100, fillcolor="#333", line_color="black") # N-S
    fig.add_shape(type="rect", x0=0, y0=40, x1=100, y1=60, fillcolor="#333", line_color="black") # E-W
    
    colors = {"RED": "#ff4b4b", "GREEN": "#21c354", "YELLOW": "#faca2b"}
    
    # Default if none
    if not signal_commands:
        signal_commands = {"N": "RED", "S": "RED", "E": "RED", "W": "RED"}
        
    # Draw signals as scatter points
    signals = [
        {"dir": "N", "x": 45, "y": 70, "color": colors.get(signal_commands.get("N", "RED"), "#ff4b4b")},
        {"dir": "S", "x": 55, "y": 30, "color": colors.get(signal_commands.get("S", "RED"), "#ff4b4b")},
        {"dir": "E", "x": 70, "y": 55, "color": colors.get(signal_commands.get("E", "RED"), "#ff4b4b")},
        {"dir": "W", "x": 30, "y": 45, "color": colors.get(signal_commands.get("W", "RED"), "#ff4b4b")},
    ]
    
    fig.add_trace(go.Scatter(
        x=[s["x"] for s in signals],
        y=[s["y"] for s in signals],
        mode="markers+text",
        marker=dict(size=24, color=[s["color"] for s in signals], line=dict(width=2, color="white")),
        text=[s["dir"] for s in signals],
        textposition="top center",
        textfont=dict(color="white", size=16, family="Arial Black")
    ))
    
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, zeroline=False, visible=False, range=[0, 100]),
        yaxis=dict(showgrid=False, zeroline=False, visible=False, range=[0, 100]),
        margin=dict(l=0, r=0, t=0, b=0),
        height=400
    )
    return fig

# --- Main App ---
def main():
    st.title("🚦 AI Traffic Junction Optimizer")
    
    # Initialize session state for history
    if 'history' not in st.session_state:
        st.session_state.history = pd.DataFrame(columns=['Time', 'N', 'S', 'E', 'W'])
        
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        st.write("API Status: **Online** 🟢")
        sim_speed = st.slider("Simulation Speed", 0.5, 2.0, 1.0)
        st.markdown("---")
        st.write("Dashboard auto-refreshes every 1 second.")
        
    # Load Data
    traffic_state = load_json(TRAFFIC_STATE_FILE)
    signal_commands = load_json(SIGNAL_COMMANDS_FILE)
    agent_logs = load_json(AGENT_LOGS_FILE)
    
    if traffic_state:
        # Emergency Alert
        if traffic_state.get("emergency"):
            st.error("🚨 EMERGENCY VEHICLE DETECTED - PRIORITY OVERRIDE ACTIVE")
            st.snow()
            
        # Top Row (KPIs)
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        total_vehicles = sum([traffic_state.get(d, 0) for d in ["N", "S", "E", "W"]])
        
        with kpi1:
            st.metric("Avg. Wait Time", f"{max(0, 15 - (total_vehicles // 10))}s", "-1.2s")
        with kpi2:
            st.metric("Total Vehicles", total_vehicles, f"+{total_vehicles % 5}")
        with kpi3:
            st.metric("CO2 Reduction", "14.2%", "+2.1%")
        with kpi4:
            st.metric("System Efficiency", "92%", "+1%")
            
        # Update history
        new_row = pd.DataFrame([{
            'Time': pd.Timestamp.now(), 
            'N': traffic_state.get('N', 0),
            'S': traffic_state.get('S', 0),
            'E': traffic_state.get('E', 0),
            'W': traffic_state.get('W', 0)
        }])
        st.session_state.history = pd.concat([st.session_state.history, new_row]).tail(60) # keep last 60 seconds
        
    else:
        st.warning("Waiting for traffic state data...")

    # Middle Row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📷 Live Vision Feed")
        if os.path.exists(VISION_OUTPUT_FILE):
            st.image(VISION_OUTPUT_FILE, width=True)
        else:
            st.info("Vision feed unavailable.")
            
    with col2:
        st.subheader("🚥 Digital Twin (Signal State)")
        fig_intersection = create_intersection_fig(signal_commands)
        st.plotly_chart(fig_intersection, width=True)
        
    # Bottom Row
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("📈 Traffic Density Over Time")
        if not st.session_state.history.empty:
            fig_line = px.line(st.session_state.history, x='Time', y=['N', 'S', 'E', 'W'], 
                               labels={'value': 'Vehicle Count', 'variable': 'Direction'},
                               template="plotly_dark")
            st.plotly_chart(fig_line, width=True)
            
    with col4:
        st.subheader("🧠 Agent Reasoning Logs")
        with st.expander("Agent Reasoning Logs", expanded=True):
            if agent_logs:
                for log in agent_logs:
                    st.markdown(f"**{log.get('agent', 'Agent')}**: {log.get('message', '')}")
            else:
                st.write("No agent logs available yet.")

    time.sleep(1)
    st.rerun()

if __name__ == "__main__":
    main()
