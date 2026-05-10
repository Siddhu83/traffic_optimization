"""
Integration test: Verify the optimizer is properly integrated with the crew.

This script tests that:
1. The optimizer module can be imported
2. The crew can be instantiated
3. The optimizer tools are available to the crew
4. The optimizer produces valid signal commands
"""

import json
import sys
from pathlib import Path

# Add parent (src) directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from crew import TrafficCrew
from logic.optimizer import optimize, TrafficState

def test_crew_instantiation():
    """Test that the crew can be instantiated"""
    print("\n📝 Test 1: Crew Instantiation")
    print("-" * 50)
    try:
        traffic_crew = TrafficCrew()
        print("✅ TrafficCrew instantiated successfully")
        print(f"   - Gemini LLM configured: {traffic_crew.gemini_llm is not None}")
        print(f"   - Groq LLM configured: {traffic_crew.groq_llm is not None}")
        print(f"   - Optimizer initialized: {traffic_crew.optimizer is not None}")
        return True
    except Exception as e:
        print(f"❌ Failed to instantiate TrafficCrew: {e}")
        return False

def test_optimizer_tool():
    """Test the optimizer tool function"""
    print("\n📝 Test 2: Optimizer Tool Function")
    print("-" * 50)
    try:
        traffic_crew = TrafficCrew()
        
        # Test traffic scenario
        test_data = {
            'N': 25,
            'S': 5,
            'E': 10,
            'W': 8,
            'emergency': False
        }
        
        result = traffic_crew.optimize_signal_timing(test_data)
        
        print(f"✅ Optimizer tool executed successfully")
        print(f"   - Input: {test_data}")
        print(f"   - Output: {result}")
        
        # Validate output
        assert 'lane' in result, "Missing 'lane' field"
        assert 'seconds' in result, "Missing 'seconds' field"
        assert 'priority' in result, "Missing 'priority' field"
        assert 'reason' in result, "Missing 'reason' field"
        
        assert result['lane'] in ['N', 'S', 'E', 'W'], f"Invalid lane: {result['lane']}"
        assert 10 <= result['seconds'] <= 60, f"Invalid seconds: {result['seconds']}"
        
        print(f"   - Output validation: PASSED")
        return True
    except Exception as e:
        print(f"❌ Optimizer tool failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_emergency_override():
    """Test emergency override functionality"""
    print("\n📝 Test 3: Emergency Override in Tool")
    print("-" * 50)
    try:
        traffic_crew = TrafficCrew()
        
        # Test emergency scenario
        test_data = {
            'N': 5,
            'S': 25,
            'E': 10,
            'W': 8,
            'emergency': True,
            'emergency_lane': 'S'
        }
        
        result = traffic_crew.optimize_signal_timing(test_data)
        
        print(f"✅ Emergency override executed")
        print(f"   - Input: {test_data}")
        print(f"   - Output: {result}")
        
        assert result['lane'] == 'S', f"Expected lane S, got {result['lane']}"
        assert result['priority'] == True, "Priority should be True for emergency"
        assert result['seconds'] == 30, f"Emergency time should be 30s, got {result['seconds']}"
        
        print(f"   - Emergency handling: PASSED")
        return True
    except Exception as e:
        print(f"❌ Emergency override test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_stats_tracking():
    """Test statistics tracking"""
    print("\n📝 Test 4: Statistics Tracking")
    print("-" * 50)
    try:
        traffic_crew = TrafficCrew()
        
        # Process some traffic
        for i in range(3):
            test_data = {'N': 10+i*5, 'S': 5, 'E': 8, 'W': 7, 'emergency': False}
            traffic_crew.optimize_signal_timing(test_data)
        
        # Get stats
        stats = traffic_crew.get_optimizer_stats()
        
        print(f"✅ Statistics retrieved successfully")
        print(f"   - Total vehicles processed: {stats['total_vehicles_processed']}")
        print(f"   - Total time saved: {stats['total_time_saved_seconds']:.2f}s")
        print(f"   - CO2 saved: {stats['co2_saved_grams']:.2f}g ({stats['co2_saved_kg']:.4f}kg)")
        
        assert stats['total_vehicles_processed'] > 0, "Should have processed vehicles"
        
        print(f"   - Statistics tracking: PASSED")
        return True
    except Exception as e:
        print(f"❌ Statistics tracking failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_stats_reset():
    """Test statistics reset"""
    print("\n📝 Test 5: Statistics Reset")
    print("-" * 50)
    try:
        traffic_crew = TrafficCrew()
        
        # Process some traffic
        test_data = {'N': 10, 'S': 5, 'E': 8, 'W': 7, 'emergency': False}
        traffic_crew.optimize_signal_timing(test_data)
        
        # Reset
        reset_result = traffic_crew.reset_optimizer_stats()
        
        print(f"✅ Statistics reset executed: {reset_result}")
        
        # Verify reset
        stats = traffic_crew.get_optimizer_stats()
        print(f"   - Total vehicles after reset: {stats['total_vehicles_processed']}")
        
        assert stats['total_vehicles_processed'] == 0, "Stats should be reset to 0"
        
        print(f"   - Reset validation: PASSED")
        return True
    except Exception as e:
        print(f"❌ Statistics reset failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_json_serialization():
    """Test that results are JSON serializable"""
    print("\n📝 Test 6: JSON Serialization")
    print("-" * 50)
    try:
        traffic_crew = TrafficCrew()
        
        test_data = {'N': 10, 'S': 5, 'E': 8, 'W': 7, 'emergency': False}
        result = traffic_crew.optimize_signal_timing(test_data)
        
        # Try to serialize to JSON
        json_str = json.dumps(result)
        parsed = json.loads(json_str)
        
        print(f"✅ JSON serialization successful")
        print(f"   - Original: {result}")
        print(f"   - JSON: {json_str}")
        print(f"   - Parsed back: {parsed}")
        
        assert parsed == result, "Parsed result should match original"
        
        print(f"   - Serialization test: PASSED")
        return True
    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests"""
    print("=" * 70)
    print("🚀 CREW + OPTIMIZER INTEGRATION TEST SUITE")
    print("=" * 70)
    
    tests = [
        test_crew_instantiation,
        test_optimizer_tool,
        test_emergency_override,
        test_stats_tracking,
        test_stats_reset,
        test_json_serialization
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} raised exception: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"📊 INTEGRATION TEST RESULTS: {passed} passed, {failed} failed out of {passed + failed}")
    print("=" * 70)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
