# Quick Reference: Using the Traffic Optimizer

## 📦 What You Have Now

### Core Module: `src/logic/optimizer.py`
The complete optimization engine with:
- ✅ Adaptive signal timing (15 + 2 per vehicle seconds)
- ✅ Emergency vehicle override (30s priority)
- ✅ Starvation prevention (120+ second detection)
- ✅ Deadlock handling (N→S→E→W cycling)
- ✅ Efficiency metrics (CO2 & time savings)
- ✅ Full Pydantic validation
- ✅ Detailed logging

### Test Suite: `src/logic/test_optimizer.py`
- 10 traffic scenarios
- 4 integration tests
- **Result: 14/14 PASSED ✅**

---

## 🔗 Integration with Crew

The optimizer is **already integrated** into your crew.py:

### In `src/crew.py`:
```python
# Import the optimizer
from logic.optimizer import optimize, get_optimizer, TrafficOptimizer

# In TrafficCrew class:
def optimize_signal_timing(self, traffic_data: dict) -> dict:
    """Tool available to Signal Strategist agent"""
    return optimize(traffic_data)

def get_optimizer_stats(self) -> dict:
    """Get cumulative impact statistics"""
    return self.optimizer.get_impact_stats()
```

### Usage in Your Agents:
The Signal Strategist agent can now call:
```python
result = self.optimize_signal_timing({
    'N': 10, 'S': 5, 'E': 8, 'W': 7,
    'emergency': False
})
```

---

## 📥 Input Format

Your traffic data must follow this structure:

```json
{
  "N": 10,           // Number of vehicles at North lane
  "S": 5,            // Number of vehicles at South lane
  "E": 8,            // Number of vehicles at East lane
  "W": 7,            // Number of vehicles at West lane
  "emergency": false // Is there an emergency vehicle?
}
```

**Optional (only if emergency=true):**
```json
{
  "emergency_lane": "N"  // Which lane has the emergency? (N|S|E|W)
}
```

---

## 📤 Output Format

All signal commands returned are JSON-serializable:

```json
{
  "lane": "N",                           // Which lane gets green
  "seconds": 35,                         // Duration of green light
  "priority": false,                     // Emergency mode?
  "reason": "Lane N has highest density" // Decision explanation
}
```

---

## 🚀 How It Works: Decision Flowchart

```
Traffic Data Input
    ↓
1. Emergency Check?
    ├─ YES → FORCE_GREEN (lane, 30s, priority=True)
    ├─ NO → Continue
2. Starvation Check? (any lane >120s without green)
    ├─ YES → Prioritize starving lane
    ├─ NO → Continue
3. Deadlock Check? (all lanes = 0 vehicles)
    ├─ YES → Cycle mode (10s per lane fairness)
    ├─ NO → Continue
4. Normal Mode: Pick highest density lane
    └─ Calculate time: 15 + (vehicles × 2), capped 10-60s
    
Output: SignalCommand (lane, seconds, priority, reason)
```

---

## ⚙️ Configuration Constants

Easy to adjust if needed:

```python
# In src/logic/optimizer.py TrafficOptimizer class:

BASE_GREEN_TIME = 15              # seconds
ADDITIONAL_TIME_PER_VEHICLE = 2   # seconds per vehicle
MAX_GREEN_TIME = 60               # seconds (upper limit)
MIN_GREEN_TIME = 10               # seconds (pedestrian safety)
EMERGENCY_GREEN_TIME = 30         # seconds (ambulance)
STARVATION_THRESHOLD = 120        # seconds (fairness)
DEADLOCK_CYCLE_TIME = 10          # seconds (edge case)
CO2_PER_10_SECONDS_IDLE = 15      # grams (efficiency metric)
```

---

## 📊 Statistics & Reporting

Get impact metrics for your storyteller:

```python
from src.logic.optimizer import get_optimizer

optimizer = get_optimizer()
stats = optimizer.get_impact_stats()

# Returns:
{
    'total_vehicles_processed': 1000,
    'total_time_saved_seconds': 2500.5,
    'co2_saved_grams': 7500.0,
    'co2_saved_kg': 7.5
}
```

---

## ✅ Test It

Run the complete test suite:

```bash
cd c:\Users\Vara Prasad\OneDrive\Desktop\traffic_optimization
python src\logic\test_optimizer.py
```

Expected output:
```
===============================================================
🚦 TRAFFIC OPTIMIZER - 10 SCENARIO TEST SUITE
===============================================================

✅ Scenario 1 PASSED: Lane N has highest density (30 vehicles)
✅ Scenario 2 PASSED: Lane W has highest density (6 vehicles)
✅ Scenario 3 PASSED: Emergency vehicle detected - PRIORITY MODE
... (10 scenarios total)
✅ Pydantic validation PASSED
✅ Efficiency metrics PASSED
✅ Impact stats PASSED
✅ JSON serialization PASSED

===============================================================
📊 TEST RESULTS: 14 passed, 0 failed out of 14
===============================================================
```

---

## 🎯 Key Features for Each Team Member

### For the **Architect** (crew.py):
- Tools are ready: `optimize_signal_timing()`, `get_optimizer_stats()`
- Input: traffic data from Vision module
- Output: JSON signal commands
- Fully compatible with crewai agents

### For the **Vision Spec**:
- Optimizer expects: N, S, E, W vehicle counts
- Must include `emergency` boolean flag
- Optional: `emergency_lane` field
- Format: dictionary with these exact keys

### For the **UI Lead** (dashboard):
- Signal commands are JSON-serializable
- Include `reason` field for explanation overlay
- Can display: lane indicator, countdown timer, priority badge
- Mock data available in test file

### For the **Storyteller**:
- Call `get_optimizer_stats()` for impact metrics
- Total vehicles processed
- Time saved (in seconds)
- CO2 prevented (in grams and kg)
- Build narrative around these numbers!

---

## 🐛 Debugging / Logging

The optimizer includes detailed logging. All decisions are logged:

```python
import logging
logging.basicConfig(level=logging.INFO)

# You'll see:
# INFO: 🚦 Traffic Optimizer initialized
# INFO: ✅ Lane N: 30 vehicles → 60s green time
# INFO: 📊 Efficiency: 225.0s saved, 675.0g CO2 prevented
# WARNING: 🚨 EMERGENCY DETECTED in lane E!
# WARNING: ⚠️ STARVATION DETECTED: Lane S hasn't had green in 130s
# INFO: 🔄 DEADLOCK MODE: Cycling to lane N
```

---

## 📚 Files Overview

```
src/logic/
├── __init__.py
│   └── Exports: TrafficOptimizer, TrafficState, SignalCommand, optimize()
│
├── optimizer.py  (500+ lines)
│   ├── TrafficState - Input validation model
│   ├── SignalCommand - Output model
│   ├── LaneMetrics - Internal metrics model
│   ├── TrafficOptimizer - Main class
│   │   ├── calculate_green_time()
│   │   ├── emergency_override()
│   │   ├── check_starvation()
│   │   ├── handle_deadlock()
│   │   ├── calculate_efficiency_metrics()
│   │   ├── optimize_signal()
│   │   └── get_impact_stats()
│   └── Public functions:
│       ├── optimize() - For crew integration
│       └── get_optimizer() - Singleton pattern
│
└── test_optimizer.py (330+ lines)
    ├── 10 Traffic Scenarios
    ├── 4 Integration Tests
    └── run_all_scenarios() - Test runner
```

---

## 🎓 Example: Understanding a Decision

**Input:**
```python
traffic = {
    'N': 20,        # 20 cars at North
    'S': 3,         # 3 cars at South  
    'E': 15,        # 15 cars at East
    'W': 8,         # 8 cars at West
    'emergency': False
}
```

**Decision Process:**
1. ✅ No emergency → Continue
2. ✅ No starvation → Continue
3. ✅ Not deadlock (68 total vehicles) → Continue
4. 🎯 Find max: N=20 (highest)
5. 📐 Calculate: 15 + (20 × 2) = 55s (within 10-60 cap)
6. 📊 Efficiency: 30+ seconds of savings, ~90g CO2 prevented

**Output:**
```json
{
  "lane": "N",
  "seconds": 55,
  "priority": false,
  "reason": "Lane N has highest density (20 vehicles)"
}
```

---

## 💡 Pro Tips

1. **For faster simulations:** Feed traffic data rapidly to test different scenarios
2. **For reporting:** Call `get_optimizer_stats()` periodically
3. **For debugging:** Check logs for detailed decision reasoning
4. **For testing:** Use the 10 scenarios as reference patterns
5. **For production:** The starvation check makes this real-world ready

---

**Ready to integrate? Your Logic Engineer's work is complete! 🚀**
