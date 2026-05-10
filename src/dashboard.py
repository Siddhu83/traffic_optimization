import json
import random
import time
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from logic.optimizer import optimize

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
TRAFFIC_STATE_FILE = DATA_DIR / "traffic_state.json"
SIGNAL_COMMANDS_FILE = DATA_DIR / "signal_commands.json"

LANE_ORDER = ["N", "E", "S", "W"]

SIMULATION_LAYOUT = {
    "N": {"axis": "y", "start": 1.05, "end": 0.45, "offset": -0.05, "label": "North"},
    "S": {"axis": "y", "start": -0.05, "end": 0.55, "offset": 0.05, "label": "South"},
    "E": {"axis": "x", "start": -0.05, "end": 0.45, "offset": -0.05, "label": "East"},
    "W": {"axis": "x", "start": 1.05, "end": 0.55, "offset": 0.05, "label": "West"},
}

COLORS = {
    "green": "#00ff88",
    "red": "#ff4d4d",
    "gray": "#222222",
    "road": "#1a1a1a",
    "vehicle": "#8ad4ff",
    "priority": "#ffcc00",
    "ambulance": "#ff3333",
    "lane": "#f5f7fb",
}


def load_json(file_path):
    if file_path.exists():
        try:
            return json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
    return None


def generate_demo_traffic(state):
    if "demo_counts" not in st.session_state:
        st.session_state.demo_counts = {"N": 9, "E": 14, "S": 7, "W": 11}

    surge_lane = LANE_ORDER[(state.refresh_count // 12) % len(LANE_ORDER)]
    for lane in LANE_ORDER:
        arrival = random.randint(0, 1)
        if lane == surge_lane:
            arrival += random.randint(1, 3)
        if lane == state.active_lane and state.signal_countdown > 0:
            arrival -= random.randint(2, 4)
        st.session_state.demo_counts[lane] = max(1, min(28, st.session_state.demo_counts[lane] + arrival))

    base = dict(st.session_state.demo_counts)

    emergency = (state.refresh_count % 34 == 0) or random.random() < 0.035
    emergency_lane = None
    if emergency:
        emergency_lane = random.choice(LANE_ORDER)
        base[emergency_lane] = max(base[emergency_lane], 8)
        st.session_state.demo_counts[emergency_lane] = base[emergency_lane]

    state = {"N": base["N"], "S": base["S"], "E": base["E"], "W": base["W"], "emergency": emergency}
    if emergency_lane:
        state["emergency_lane"] = emergency_lane
    return state


def build_signal_command(traffic_data, emergency_active):
    optimizer_input = {lane: int(traffic_data.get(lane, 0)) for lane in ["N", "S", "E", "W"]}
    optimizer_input["emergency"] = bool(emergency_active)
    if emergency_active:
        optimizer_input["emergency_lane"] = traffic_data.get(
            "emergency_lane",
            max(optimizer_input, key=lambda key: optimizer_input[key] if key in LANE_ORDER else -1),
        )
    return optimize(optimizer_input)


def get_simulation_state():
    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = time.time()
    if "refresh_count" not in st.session_state:
        st.session_state.refresh_count = 0
    if "vehicle_positions" not in st.session_state:
        st.session_state.vehicle_positions = {lane: [] for lane in LANE_ORDER}
    if "signal_countdown" not in st.session_state:
        st.session_state.signal_countdown = 0
    if "active_lane" not in st.session_state:
        st.session_state.active_lane = None
    if "emergency_active" not in st.session_state:
        st.session_state.emergency_active = False
    if "ai_messages" not in st.session_state:
        st.session_state.ai_messages = []
    if "force_ambulance_ticks" not in st.session_state:
        st.session_state.force_ambulance_ticks = 0
    if "force_ambulance_lane" not in st.session_state:
        st.session_state.force_ambulance_lane = "N"
    if "current_command" not in st.session_state:
        st.session_state.current_command = None

    st.session_state.refresh_count += 1
    return st.session_state


def lane_point(lane, position, index):
    config = SIMULATION_LAYOUT[lane]
    spacing = 0.05 * (index % 3)
    if lane == "N":
        return 0.45 + (index % 2) * 0.08, config["start"] - position * (config["start"] - config["end"]) - spacing
    if lane == "S":
        return 0.55 - (index % 2) * 0.08, config["start"] + position * (config["end"] - config["start"]) + spacing
    if lane == "E":
        return config["start"] + position * (config["end"] - config["start"]) + spacing, 0.55 - (index % 2) * 0.08
    if lane == "W":
        return config["start"] - position * (config["start"] - config["end"]) - spacing, 0.45 + (index % 2) * 0.08
    return 0.5, 0.5


def initialize_vehicle_positions(traffic_data):
    positions = {}
    for lane in LANE_ORDER:
        count = min(max(traffic_data.get(lane, 1), 1), 12)
        positions[lane] = [max(0.0, min(1.0, 1.0 - i * 0.05)) for i in range(count)]
    return positions


def update_vehicle_positions(state, traffic_data, active_lane):
    target_counts = {lane: min(max(traffic_data.get(lane, 1), 1), 12) for lane in LANE_ORDER}
    for lane in LANE_ORDER:
        current = state.vehicle_positions[lane]
        if len(current) < target_counts[lane]:
            for i in range(len(current), target_counts[lane]):
                current.append(max(0.0, min(1.0, 1.0 - i * 0.05)))
        elif lane == active_lane and len(current) > target_counts[lane]:
            state.vehicle_positions[lane] = current[:target_counts[lane]]
            current = state.vehicle_positions[lane]

        updated = []
        for position in current:
            if lane == active_lane and state.signal_countdown > 0:
                new_position = min(1.05, position + 0.08)
            else:
                new_position = position
            if new_position < 1.05:
                updated.append(new_position)
        if len(updated) < target_counts[lane]:
            updated += [max(0.0, min(1.0, 0.0 + 0.02 * i)) for i in range(target_counts[lane] - len(updated))]
        if lane == active_lane:
            state.vehicle_positions[lane] = updated[:target_counts[lane]]
        else:
            state.vehicle_positions[lane] = updated[: max(len(updated), target_counts[lane])]


def build_intersection_figure(traffic_data, command, state):
    fig = go.Figure()
    fig.update_layout(
        paper_bgcolor="#080b12",
        plot_bgcolor="#080b12",
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False, range=[-0.15, 1.15]),
        yaxis=dict(visible=False, range=[-0.15, 1.15]),
        height=620,
    )

    fig.add_shape(type="rect", x0=0.35, y0=-0.15, x1=0.65, y1=1.15, fillcolor=COLORS["road"], line=dict(width=0))
    fig.add_shape(type="rect", x0=-0.15, y0=0.35, x1=1.15, y1=0.65, fillcolor=COLORS["road"], line=dict(width=0))
    fig.add_shape(type="line", x0=0.5, y0=-0.15, x1=0.5, y1=1.15, line=dict(color="#f7f7f7", width=1, dash="dash"))
    fig.add_shape(type="line", x0=-0.15, y0=0.5, x1=1.15, y1=0.5, line=dict(color="#f7f7f7", width=1, dash="dash"))

    fig.add_shape(type="rect", x0=0.4, y0=0.4, x1=0.6, y1=0.6, fillcolor="#111111", line=dict(color="#444444"))

    for lane in LANE_ORDER:
        x, y = 0.5, 0.5
        if lane == "N":
            x, y = 0.5, 0.75
        if lane == "S":
            x, y = 0.5, 0.25
        if lane == "E":
            x, y = 0.25, 0.5
        if lane == "W":
            x, y = 0.75, 0.5
        color = COLORS["green"] if command["lane"] == lane else COLORS["red"]
        fig.add_trace(
            go.Scatter(
                x=[x],
                y=[y],
                mode="markers+text",
                marker=dict(size=32, color=color, line=dict(color="#ffffff", width=1.5)),
                text=[lane],
                textposition="middle center",
                hoverinfo="none",
            )
        )
        fig.add_annotation(
            x=x,
            y=y + 0.08,
            text=f"{lane} signal",
            showarrow=False,
            font=dict(color="#b3b3b3", size=10),
        )

    car_x, car_y, car_symbol, car_hover = [], [], [], []
    ambulance_x, ambulance_y, ambulance_hover = [], [], []
    emergency_lane = traffic_data.get("emergency_lane") or command.get("lane")
    lane_symbols = {"N": "triangle-down", "S": "triangle-up", "E": "triangle-right", "W": "triangle-left"}
    for lane in LANE_ORDER:
        for idx, position in enumerate(state.vehicle_positions[lane]):
            x, y = lane_point(lane, position, idx)
            is_ambulance = bool(command.get("priority")) and lane == emergency_lane and idx == 0
            if is_ambulance:
                ambulance_x.append(x)
                ambulance_y.append(y)
                ambulance_hover.append(f"Ambulance in {lane} lane")
            else:
                car_x.append(x)
                car_y.append(y)
                car_symbol.append(lane_symbols[lane])
                car_hover.append(f"Car in {lane} lane #{idx + 1}")

    fig.add_trace(
        go.Scatter(
            x=car_x,
            y=car_y,
            mode="markers",
            marker=dict(
                size=18,
                color=COLORS["vehicle"],
                symbol=car_symbol,
                line=dict(color="#dff5ff", width=1.5),
                opacity=0.95,
            ),
            hoverinfo="text",
            hovertext=car_hover,
            name="Cars",
            showlegend=False,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=ambulance_x,
            y=ambulance_y,
            mode="markers+text",
            marker=dict(
                size=30,
                color=COLORS["ambulance"],
                symbol="diamond",
                line=dict(color="#ffffff", width=2),
            ),
            text=["AMB"] * len(ambulance_x),
            textfont=dict(color="#ffffff", size=8, family="Arial Black"),
            textposition="middle center",
            hoverinfo="text",
            hovertext=ambulance_hover,
            name="Ambulance",
            showlegend=False,
        )
    )

    for lane in LANE_ORDER:
        label_x, label_y = {"N": (0.5, 1.1), "S": (0.5, -0.1), "E": (-0.1, 0.5), "W": (1.1, 0.5)}[lane]
        fig.add_annotation(
            x=label_x,
            y=label_y,
            text=f"{lane}: {traffic_data.get(lane, 0)}",
            showarrow=False,
            font=dict(color=COLORS["lane"], size=13),
            bgcolor="rgba(8, 11, 18, 0.75)",
            bordercolor="#2c3b55",
            borderpad=4,
        )

    fig.add_annotation(x=0.5, y=1.05, text="LIVE AI TRAFFIC SIMULATION", showarrow=False, font=dict(color="#ffffff", size=16))
    if state.emergency_active:
        fig.add_annotation(
            x=0.5,
            y=1.0,
            text=f"AMBULANCE PRIORITY ACTIVE: {command['lane']} LANE",
            showarrow=False,
            font=dict(color=COLORS["ambulance"], size=14, family="Arial Black"),
            bgcolor="rgba(255, 51, 51, 0.14)",
            bordercolor=COLORS["ambulance"],
            borderpad=5,
        )

    fig.update_layout(transition=dict(duration=400, easing="cubic-in-out"))
    return fig


def format_reasoning(traffic_data, command, state):
    traffic_messages = [f"{lane} lane: {traffic_data[lane]} vehicles" for lane in LANE_ORDER]
    ai_messages = [
        f"[AI Strategist] {traffic_messages[0]}",
        f"[AI Strategist] {traffic_messages[1]}",
        f"[AI Strategist] {traffic_messages[2]}",
        f"[AI Strategist] {traffic_messages[3]}",
        f"[Signal Brain] Executing green for {command['lane']} lane for {command['seconds']}s",
        f"[Signal Brain] Reason: {command['reason']}",
    ]
    if state.emergency_active:
        ai_messages.append("[Emergency Handler] Ambulance detected - priority override engaged")
    return ai_messages


def render_dashboard():
    st.set_page_config(page_title="Live Junction Simulator", page_icon="🚦", layout="wide")

    st.markdown(
        """
        <style>
        .reportview-container {background: #060809;}
        .stApp {background: #060809; color: #ffffff;}
        .card {background: #0f1620; border: 1px solid #1b2a45; border-radius: 18px; padding: 18px;}
        .neon {color: #9dfcfd;}
        .small-muted {color: #8a98ad; font-size: 0.95rem;}
        .signal-pill {padding: 8px 14px; border-radius: 999px; font-weight: 700;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    state = get_simulation_state()
    with st.sidebar:
        st.markdown("### Demo Controls")
        state.force_ambulance_lane = st.selectbox(
            "Ambulance lane",
            LANE_ORDER,
            index=LANE_ORDER.index(state.force_ambulance_lane),
        )
        if st.button("Trigger ambulance", use_container_width=True):
            state.force_ambulance_ticks = 10

    traffic_data = load_json(TRAFFIC_STATE_FILE)
    traffic_available = traffic_data is not None and all(k in traffic_data for k in LANE_ORDER)
    if not traffic_available:
        traffic_data = generate_demo_traffic(state)
        demo_message = "DEMO MODE: generating synthetic traffic in the absence of live sensor feeds."
    else:
        demo_message = "LIVE MODE: using the latest `data/traffic_state.json` from Vision."

    if state.force_ambulance_ticks > 0:
        traffic_data["emergency"] = True
        traffic_data["emergency_lane"] = state.force_ambulance_lane
        traffic_data[state.force_ambulance_lane] = max(traffic_data.get(state.force_ambulance_lane, 0), 8)
        if "demo_counts" in st.session_state:
            st.session_state.demo_counts[state.force_ambulance_lane] = traffic_data[state.force_ambulance_lane]
        state.force_ambulance_ticks -= 1

    command_data = load_json(SIGNAL_COMMANDS_FILE)
    command_available = (
        traffic_available
        and command_data is not None
        and command_data.get("lane") in LANE_ORDER
        and "seconds" in command_data
    )
    should_reoptimize = (
        state.current_command is None
        or state.signal_countdown <= 0
        or traffic_data.get("emergency", False)
    )
    if should_reoptimize:
        command = command_data if command_available else build_signal_command(traffic_data, traffic_data.get("emergency", False))
        if not traffic_available:
            command = dict(command)
            command["seconds"] = min(int(command["seconds"]), 10 if command.get("priority") else 8)
        state.current_command = command
        state.active_lane = command["lane"]
        state.signal_countdown = int(command["seconds"])
    else:
        command = state.current_command

    if traffic_data.get("emergency", False) or command.get("priority", False):
        state.emergency_active = True
    else:
        state.emergency_active = False

    if state.signal_countdown > 0:
        state.signal_countdown -= 1
    else:
        state.active_lane = command["lane"]
        state.signal_countdown = int(command["seconds"])

    update_vehicle_positions(state, traffic_data, state.active_lane)
    displayed_counts = {lane: len(state.vehicle_positions[lane]) for lane in LANE_ORDER}

    header_col1, header_col2 = st.columns([3, 2])
    with header_col1:
        st.markdown("## 🚦 Smart City Traffic Control Center")
        st.markdown(f"<div class='small-muted'>{demo_message}</div>", unsafe_allow_html=True)
    with header_col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"### Current Green Lane")
        st.markdown(f"<div class='signal-pill' style='background:{COLORS['green']};color:#030b06;'>{state.active_lane}</div>", unsafe_allow_html=True)
        st.markdown(f"### Countdown")
        st.markdown(f"<div class='signal-pill' style='background:#181f2d;color:#ffffff;'>{state.signal_countdown}s</div>", unsafe_allow_html=True)
        st.markdown(f"### Vehicles Active")
        st.markdown(f"<div class='signal-pill' style='background:#121827;color:#ffffff;'>{sum(displayed_counts.values())}</div>", unsafe_allow_html=True)
        st.markdown(f"### AI Status")
        st.markdown(f"<div class='signal-pill' style='background:#131c2b;color:{COLORS['green']};'>OPTIMIZING</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    sim_col, panel_col = st.columns([3, 1])
    with sim_col:
        st.plotly_chart(build_intersection_figure({**traffic_data, **displayed_counts}, command, state), use_container_width=True)
    with panel_col:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("## Live AI Reasoning")
        reasoning = format_reasoning(traffic_data, command, state)
        for message in reasoning:
            st.markdown(f"- {message}")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card' style='margin-top: 18px;'>", unsafe_allow_html=True)
        st.markdown("## Signal Command")
        st.markdown(f"**Lane:** {command['lane']}")
        st.markdown(f"**Duration:** {command['seconds']}s")
        st.markdown(f"**Priority:** {command.get('priority', False)}")
        st.markdown(f"**Reason:** {command['reason']}")
        st.markdown("</div>", unsafe_allow_html=True)

    if state.emergency_active:
        st.toast("🚑 PRIORITY OVERRIDE ACTIVE", icon="🚑")
        st.markdown(
            "<div class='card' style='border: 1px solid #ff3b3b; background: rgba(255, 59, 59, 0.08); padding: 14px;'>"
            "<strong>EMERGENCY MODE:</strong> Ambulance priority is active, clearing the way in real time.</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("### Data Sources")
    st.markdown(f"- Traffic state: `{TRAFFIC_STATE_FILE}`")
    st.markdown(f"- Signal commands: `{SIGNAL_COMMANDS_FILE}`")

    time.sleep(1)
    st.rerun()


if __name__ == "__main__":
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    render_dashboard()
