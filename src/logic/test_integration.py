"""
Integration test: verify the optimizer is connected to the demo orchestration.

This script intentionally avoids external LLM calls. The demo uses the local
TrafficOptimizer through TrafficCrew so it remains reliable offline.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from crew import TrafficCrew


def test_crew_instantiation():
    print("\nTest 1: Crew instantiation")
    print("-" * 50)
    try:
        traffic_crew = TrafficCrew()
        assert traffic_crew.optimizer is not None
        assert "traffic_analyzer" in traffic_crew.agents_config
        assert "optimize_signals_task" in traffic_crew.tasks_config
        assert hasattr(traffic_crew, "kickoff")
        print("PASS: TrafficCrew instantiated with optimizer and configs")
        return True
    except Exception as exc:
        print(f"FAIL: TrafficCrew instantiation failed: {exc}")
        return False


def test_optimizer_tool():
    print("\nTest 2: Optimizer tool")
    print("-" * 50)
    try:
        traffic_crew = TrafficCrew()
        traffic_crew.reset_optimizer_stats()
        test_data = {"N": 25, "S": 5, "E": 10, "W": 8, "emergency": False}
        result = traffic_crew.optimize_signal_timing(test_data)

        assert result["lane"] == "N"
        assert result["seconds"] == 60
        assert result["priority"] is False
        assert "reason" in result
        print(f"PASS: Optimizer selected {result['lane']} for {result['seconds']}s")
        return True
    except Exception as exc:
        print(f"FAIL: Optimizer tool failed: {exc}")
        return False


def test_emergency_override():
    print("\nTest 3: Emergency override")
    print("-" * 50)
    try:
        traffic_crew = TrafficCrew()
        traffic_crew.reset_optimizer_stats()
        test_data = {
            "N": 5,
            "S": 25,
            "E": 10,
            "W": 8,
            "emergency": True,
            "emergency_lane": "S",
        }
        result = traffic_crew.optimize_signal_timing(test_data)

        assert result["lane"] == "S"
        assert result["seconds"] == 30
        assert result["priority"] is True
        print("PASS: Emergency lane received immediate priority")
        return True
    except Exception as exc:
        print(f"FAIL: Emergency override failed: {exc}")
        return False


def test_kickoff_writes_signal_command():
    print("\nTest 4: Kickoff writes signal command")
    print("-" * 50)
    try:
        traffic_crew = TrafficCrew()
        test_data = {"N": 10, "S": 5, "E": 8, "W": 7, "emergency": False}
        result = traffic_crew.kickoff(inputs={"traffic_data": json.dumps(test_data)})
        parsed = json.loads(result.raw)

        output_file = Path(__file__).parents[2] / "data" / "signal_commands.json"
        saved = json.loads(output_file.read_text(encoding="utf-8"))

        assert parsed == saved
        assert saved["lane"] in ["N", "S", "E", "W"]
        assert isinstance(saved["seconds"], int)
        print(f"PASS: signal_commands.json saved with lane {saved['lane']}")
        return True
    except Exception as exc:
        print(f"FAIL: Kickoff write failed: {exc}")
        return False


def test_stats_tracking_and_reset():
    print("\nTest 5: Statistics tracking and reset")
    print("-" * 50)
    try:
        traffic_crew = TrafficCrew()
        traffic_crew.reset_optimizer_stats()
        traffic_crew.optimize_signal_timing({"N": 10, "S": 5, "E": 8, "W": 7, "emergency": False})

        stats = traffic_crew.get_optimizer_stats()
        assert stats["total_vehicles_processed"] == 30
        assert stats["total_time_saved_seconds"] >= 0

        traffic_crew.reset_optimizer_stats()
        reset_stats = traffic_crew.get_optimizer_stats()
        assert reset_stats["total_vehicles_processed"] == 0
        print("PASS: Stats increment and reset correctly")
        return True
    except Exception as exc:
        print(f"FAIL: Stats tracking failed: {exc}")
        return False


def test_json_serialization():
    print("\nTest 6: JSON serialization")
    print("-" * 50)
    try:
        traffic_crew = TrafficCrew()
        result = traffic_crew.optimize_signal_timing({"N": 10, "S": 5, "E": 8, "W": 7, "emergency": False})
        json_str = json.dumps(result)
        assert json.loads(json_str) == result
        print("PASS: Signal command is JSON serializable")
        return True
    except Exception as exc:
        print(f"FAIL: JSON serialization failed: {exc}")
        return False


def main():
    print("=" * 70)
    print("CREW + OPTIMIZER INTEGRATION TEST SUITE")
    print("=" * 70)

    tests = [
        test_crew_instantiation,
        test_optimizer_tool,
        test_emergency_override,
        test_kickoff_writes_signal_command,
        test_stats_tracking_and_reset,
        test_json_serialization,
    ]

    passed = 0
    failed = 0
    for test_func in tests:
        if test_func():
            passed += 1
        else:
            failed += 1

    print("\n" + "=" * 70)
    print(f"INTEGRATION TEST RESULTS: {passed} passed, {failed} failed out of {passed + failed}")
    print("=" * 70)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
