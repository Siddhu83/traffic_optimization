"""
Test Suite for Traffic Signal Optimizer

Tests 10 different traffic scenarios to validate the optimization logic.
Each scenario tests a different aspect of the system.

Author: Logic Engineer
"""

import json
import sys
import io
from datetime import datetime, timedelta
from optimizer import (
    TrafficOptimizer,
    TrafficState,
    SignalCommand,
    get_optimizer
)

# Fix for Windows PowerShell Unicode encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class TestTrafficOptimizer:
    """Comprehensive test suite for traffic optimization"""

    # ========== SCENARIO 1: Heavy North Traffic ==========
    def test_scenario_1_heavy_north(self):
        """
        Scenario 1: Heavy North, Empty South
        Expected: Lane N gets green light with maximum time
        """
        optimizer = TrafficOptimizer()
        traffic_data = {'N': 30, 'S': 0, 'E': 5, 'W': 3, 'emergency': False}
        command = optimizer.optimize_signal(traffic_data)

        assert command.lane == 'N', "North lane should get priority"
        assert command.seconds == 60, f"Expected 60s (max), got {command.seconds}s"
        assert command.priority == False, "Should not be priority mode"
        print(f"✅ Scenario 1 PASSED: {command.reason}")
        return True

    # ========== SCENARIO 2: Empty South Only ==========
    def test_scenario_2_heavy_south(self):
        """
        Scenario 2: All lanes busy except South is empty
        Expected: South lane should cycle for fairness
        """
        optimizer = TrafficOptimizer()
        traffic_data = {'N': 5, 'S': 0, 'E': 4, 'W': 6, 'emergency': False}
        command = optimizer.optimize_signal(traffic_data)

        assert command.lane == 'W', "West lane should get priority (highest density)"
        assert command.seconds == int(15 + (6 * 2)), f"Expected 27s, got {command.seconds}s"
        print(f"✅ Scenario 2 PASSED: {command.reason}")
        return True

    # ========== SCENARIO 3: Emergency Vehicle Detection ==========
    def test_scenario_3_emergency_east(self):
        """
        Scenario 3: Emergency vehicle in East lane
        Expected: Immediate green for East, 30 seconds
        """
        optimizer = TrafficOptimizer()
        traffic_data = {
            'N': 20, 'S': 15, 'E': 5, 'W': 18,
            'emergency': True,
            'emergency_lane': 'E'
        }
        command = optimizer.optimize_signal(traffic_data)

        assert command.lane == 'E', "Emergency lane should get immediate green"
        assert command.seconds == 30, f"Expected 30s emergency time, got {command.seconds}s"
        assert command.priority == True, "Should be in priority mode"
        print(f"✅ Scenario 3 PASSED: {command.reason}")
        return True

    # ========== SCENARIO 4: Emergency Vehicle in Busiest Lane ==========
    def test_scenario_4_emergency_in_busy_lane(self):
        """
        Scenario 4: Emergency vehicle in the already busiest lane
        Expected: Emergency takes precedence, 30 seconds
        """
        optimizer = TrafficOptimizer()
        traffic_data = {
            'N': 5, 'S': 2, 'E': 50, 'W': 3,
            'emergency': True,
            'emergency_lane': 'E'
        }
        command = optimizer.optimize_signal(traffic_data)

        assert command.lane == 'E'
        assert command.seconds == 30, "Emergency overrides normal calculation"
        assert command.priority == True
        print(f"✅ Scenario 4 PASSED: {command.reason}")
        return True

    # ========== SCENARIO 5: Deadlock Scenario (All Lanes Empty) ==========
    def test_scenario_5_deadlock_all_empty(self):
        """
        Scenario 5: All lanes have 0 vehicles (deadlock)
        Expected: Cycle through lanes (N, S, E, W) for 10 seconds each
        """
        optimizer = TrafficOptimizer()
        traffic_data = {'N': 0, 'S': 0, 'E': 0, 'W': 0, 'emergency': False}

        # First call - should give N
        command1 = optimizer.optimize_signal(traffic_data)
        assert command1.lane == 'N', "First cycle should be North"
        assert command1.seconds == 10, f"Deadlock cycle should be 10s, got {command1.seconds}s"

        # Second call - should give S
        command2 = optimizer.optimize_signal(traffic_data)
        assert command2.lane == 'S', "Second cycle should be South"

        # Third call - should give E
        command3 = optimizer.optimize_signal(traffic_data)
        assert command3.lane == 'E', "Third cycle should be East"

        # Fourth call - should give W
        command4 = optimizer.optimize_signal(traffic_data)
        assert command4.lane == 'W', "Fourth cycle should be West"

        print(f"✅ Scenario 5 PASSED: Deadlock cycle working correctly")
        return True

    # ========== SCENARIO 6: Minimum Green Time Enforcement ==========
    def test_scenario_6_minimum_green_time(self):
        """
        Scenario 6: Very low vehicle count
        Expected: Minimum 10 seconds for pedestrian safety
        """
        optimizer = TrafficOptimizer()
        traffic_data = {'N': 0, 'S': 1, 'E': 0, 'W': 0, 'emergency': False}

        # Reset deadlock to avoid cycling
        optimizer.deadlock_counter = 0
        command = optimizer.optimize_signal(traffic_data)

        assert command.seconds >= 10, f"Green time should be >= 10s, got {command.seconds}s"
        print(f"✅ Scenario 6 PASSED: Minimum green time enforced ({command.seconds}s)")
        return True

    # ========== SCENARIO 7: Maximum Green Time Cap ==========
    def test_scenario_7_maximum_green_time_cap(self):
        """
        Scenario 7: Extreme congestion in one lane
        Expected: Green time capped at 60 seconds maximum
        """
        optimizer = TrafficOptimizer()
        traffic_data = {'N': 100, 'S': 0, 'E': 0, 'W': 0, 'emergency': False}
        command = optimizer.optimize_signal(traffic_data)

        assert command.lane == 'N'
        assert command.seconds == 60, f"Green time should be capped at 60s, got {command.seconds}s"
        print(f"✅ Scenario 7 PASSED: Maximum green time cap enforced")
        return True

    # ========== SCENARIO 8: Starvation Prevention ==========
    def test_scenario_8_starvation_prevention(self):
        """
        Scenario 8: Starvation detection and prevention
        Expected: Lane without green for 120+ seconds gets priority
        """
        optimizer = TrafficOptimizer()

        # Manually set a lane to have no green for 130 seconds
        old_time = datetime.now() - timedelta(seconds=130)
        optimizer.lane_last_green['S'] = old_time

        traffic_data = {'N': 10, 'S': 2, 'E': 10, 'W': 10, 'emergency': False}
        command = optimizer.optimize_signal(traffic_data)

        assert command.lane == 'S', "Starving lane should be prioritized"
        assert "Starvation" in command.reason, "Reason should mention starvation"
        print(f"✅ Scenario 8 PASSED: Starvation prevention working")
        return True

    # ========== SCENARIO 9: Balanced Traffic ==========
    def test_scenario_9_balanced_traffic(self):
        """
        Scenario 9: All lanes have similar vehicle counts
        Expected: Should select one lane (first in max() would be N or one with highest)
        """
        optimizer = TrafficOptimizer()
        traffic_data = {'N': 5, 'S': 5, 'E': 5, 'W': 5, 'emergency': False}
        command = optimizer.optimize_signal(traffic_data)

        # Should select one of the lanes (all have same density, so max() behavior)
        assert command.lane in ['N', 'S', 'E', 'W']
        expected_time = 15 + (5 * 2)  # 25 seconds
        assert command.seconds == expected_time
        print(f"✅ Scenario 9 PASSED: Balanced traffic handled ({command.lane} selected)")
        return True

    # ========== SCENARIO 10: Mixed Congestion with Emergency ==========
    def test_scenario_10_complex_scenario(self):
        """
        Scenario 10: Complex scenario with congestion on multiple lanes
        but emergency in a different lane
        Expected: Emergency should override density-based selection
        """
        optimizer = TrafficOptimizer()
        traffic_data = {
            'N': 25,  # High density
            'S': 3,   # Emergency here (low density)
            'E': 20,  # High density
            'W': 30,  # Highest density
            'emergency': True,
            'emergency_lane': 'S'
        }
        command = optimizer.optimize_signal(traffic_data)

        assert command.lane == 'S', "Emergency should override normal selection"
        assert command.seconds == 30, "Emergency time should be 30s"
        assert command.priority == True
        print(f"✅ Scenario 10 PASSED: Complex scenario with emergency override")
        return True

    # ========== INTEGRATION TESTS ==========

    def test_pydantic_validation(self):
        """Test Pydantic model validation"""
        optimizer = TrafficOptimizer()
        
        # Valid data
        valid_state = TrafficState(N=5, S=3, E=4, W=2, emergency=False)
        assert valid_state.N == 5
        
        # Invalid emergency_lane
        try:
            TrafficState(N=5, S=3, E=4, W=2, emergency=True, emergency_lane='X')
            assert False, "Should have raised ValueError"
        except ValueError:
            pass
        
        print(f"✅ Pydantic validation PASSED")
        return True

    def test_efficiency_metrics(self):
        """Test efficiency metrics calculation"""
        optimizer = TrafficOptimizer()
        metrics = optimizer.calculate_efficiency_metrics(green_time_seconds=30, avg_vehicles_waiting=10)

        assert 'time_saved_seconds' in metrics
        assert 'co2_saved_grams' in metrics
        assert 'vehicles_affected' in metrics
        assert metrics['vehicles_affected'] == 10
        print(f"✅ Efficiency metrics PASSED: {metrics}")
        return True

    def test_impact_stats(self):
        """Test impact statistics tracking"""
        optimizer = TrafficOptimizer()
        traffic_data = {'N': 10, 'S': 5, 'E': 8, 'W': 7, 'emergency': False}
        optimizer.optimize_signal(traffic_data)

        stats = optimizer.get_impact_stats()
        assert stats['total_vehicles_processed'] == 30
        assert stats['total_time_saved_seconds'] >= 0
        assert stats['co2_saved_grams'] >= 0
        print(f"✅ Impact stats PASSED: {stats}")
        return True

    def test_signal_command_serialization(self):
        """Test that SignalCommand can be serialized to JSON"""
        optimizer = TrafficOptimizer()
        traffic_data = {'N': 15, 'S': 0, 'E': 5, 'W': 3, 'emergency': False}
        command = optimizer.optimize_signal(traffic_data)

        # Should be JSON serializable
        json_str = json.dumps(command.model_dump())
        parsed = json.loads(json_str)

        assert parsed['lane'] in ['N', 'S', 'E', 'W']
        assert isinstance(parsed['seconds'], int)
        assert isinstance(parsed['priority'], bool)
        print(f"✅ JSON serialization PASSED: {json_str}")
        return True


def run_all_scenarios():
    """
    Convenience function to run all scenarios and print results.
    """
    print("=" * 70)
    print("🚦 TRAFFIC OPTIMIZER - 10 SCENARIO TEST SUITE")
    print("=" * 70 + "\n")

    test_suite = TestTrafficOptimizer()

    scenarios = [
        ("Scenario 1: Heavy North Traffic", test_suite.test_scenario_1_heavy_north),
        ("Scenario 2: Balanced Lanes", test_suite.test_scenario_2_heavy_south),
        ("Scenario 3: Emergency in East", test_suite.test_scenario_3_emergency_east),
        ("Scenario 4: Emergency in Busy Lane", test_suite.test_scenario_4_emergency_in_busy_lane),
        ("Scenario 5: Deadlock (All Empty)", test_suite.test_scenario_5_deadlock_all_empty),
        ("Scenario 6: Minimum Green Time", test_suite.test_scenario_6_minimum_green_time),
        ("Scenario 7: Maximum Green Time", test_suite.test_scenario_7_maximum_green_time_cap),
        ("Scenario 8: Starvation Prevention", test_suite.test_scenario_8_starvation_prevention),
        ("Scenario 9: Balanced Traffic", test_suite.test_scenario_9_balanced_traffic),
        ("Scenario 10: Complex + Emergency", test_suite.test_scenario_10_complex_scenario),
        ("Integration: Pydantic Validation", test_suite.test_pydantic_validation),
        ("Integration: Efficiency Metrics", test_suite.test_efficiency_metrics),
        ("Integration: Impact Stats", test_suite.test_impact_stats),
        ("Integration: JSON Serialization", test_suite.test_signal_command_serialization),
    ]

    passed = 0
    failed = 0

    for name, test_func in scenarios:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {name}")
            print(f"   Error: {e}\n")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {name}")
            print(f"   Exception: {e}\n")
            failed += 1

    print("\n" + "=" * 70)
    print(f"📊 TEST RESULTS: {passed} passed, {failed} failed out of {passed + failed}")
    print("=" * 70)

    return passed, failed


if __name__ == "__main__":
    # Run all scenarios
    passed, failed = run_all_scenarios()

    # Also show impact stats
    optimizer = get_optimizer()
    print("\n📈 Final Impact Stats:")
    print(json.dumps(optimizer.get_impact_stats(), indent=2))

    exit(0 if failed == 0 else 1)
