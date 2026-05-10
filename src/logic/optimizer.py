"""
Traffic Signal Optimization Module

This module provides adaptive signal timing logic for a 4-way junction (N, S, E, W).
It handles emergency vehicle prioritization, deadlock scenarios, and starvation prevention.

Author: Logic Engineer
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from pydantic import BaseModel, Field, validator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TrafficState(BaseModel):
    """Pydantic model for validated traffic state data"""
    N: int = Field(ge=0, description="Vehicle count at North lane")
    S: int = Field(ge=0, description="Vehicle count at South lane")
    E: int = Field(ge=0, description="Vehicle count at East lane")
    W: int = Field(ge=0, description="Vehicle count at West lane")
    emergency: bool = Field(default=False, description="Emergency vehicle detected")
    emergency_lane: Optional[str] = Field(None, description="Lane with emergency vehicle")

    @validator('emergency_lane')
    def validate_emergency_lane(cls, v, values):
        """Ensure emergency_lane is valid if emergency is True"""
        if values.get('emergency') and v not in ['N', 'S', 'E', 'W']:
            raise ValueError("emergency_lane must be one of: N, S, E, W")
        return v

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict) -> 'TrafficState':
        """Create from dictionary"""
        return cls(**data)


class LaneMetrics(BaseModel):
    """Metrics for a specific lane"""
    lane: str
    vehicle_count: int
    green_time: int
    priority: bool = False
    reason: str = ""


class SignalCommand(BaseModel):
    """Command to control traffic signals"""
    lane: str
    seconds: int
    priority: bool
    reason: str = ""


class TrafficOptimizer:
    """
    Main optimizer class for traffic signal timing.
    Handles adaptive green time calculation, emergency vehicle detection,
    and fairness mechanisms like starvation prevention.
    """

    # Configuration constants
    BASE_GREEN_TIME = 15  # seconds
    ADDITIONAL_TIME_PER_VEHICLE = 2  # seconds per vehicle
    MAX_GREEN_TIME = 60  # seconds
    MIN_GREEN_TIME = 10  # seconds (pedestrian safety)
    EMERGENCY_GREEN_TIME = 30  # seconds
    DEADLOCK_CYCLE_TIME = 10  # seconds per lane in deadlock
    STARVATION_THRESHOLD = 120  # seconds without green light
    CO2_PER_10_SECONDS_IDLE = 15  # grams

    def __init__(self):
        """Initialize the optimizer with lane state tracking"""
        self.lane_last_green = {
            'N': datetime.now(),
            'S': datetime.now(),
            'E': datetime.now(),
            'W': datetime.now()
        }
        self.total_vehicles_processed = 0
        self.total_time_saved = 0
        self.co2_saved = 0
        self.deadlock_counter = 0
        self.deadlock_cycle = ['N', 'S', 'E', 'W']

        logger.info("🚦 Traffic Optimizer initialized")

    def calculate_green_time(self, traffic_state: TrafficState, current_lane: str) -> int:
        """
        Calculate adaptive green light duration based on vehicle density.

        Args:
            traffic_state: Current traffic state with vehicle counts
            current_lane: The lane to calculate green time for

        Returns:
            Green time in seconds (between MIN_GREEN_TIME and MAX_GREEN_TIME)
        """
        if not isinstance(traffic_state, TrafficState):
            traffic_state = TrafficState(**traffic_state)

        # Get vehicle count for current lane
        vehicle_count = getattr(traffic_state, current_lane, 0)

        # Base formula: 15 seconds + 2 seconds per vehicle, capped at 60 seconds, min 10 seconds
        calculated_time = self.BASE_GREEN_TIME + (vehicle_count * self.ADDITIONAL_TIME_PER_VEHICLE)
        green_time = max(self.MIN_GREEN_TIME, min(calculated_time, self.MAX_GREEN_TIME))

        logger.info(
            f"✅ Lane {current_lane}: {vehicle_count} vehicles → {green_time}s green time"
        )

        return int(green_time)

    def emergency_override(self, traffic_state: TrafficState) -> Optional[SignalCommand]:
        """
        Handle emergency vehicle detection.
        Forces immediate green light if ambulance/emergency vehicle is present.

        Args:
            traffic_state: Current traffic state

        Returns:
            SignalCommand with forced green light, or None if no emergency
        """
        if not isinstance(traffic_state, TrafficState):
            traffic_state = TrafficState(**traffic_state)

        if traffic_state.emergency:
            emergency_lane = traffic_state.emergency_lane or 'N'
            logger.warning(
                f"🚨 EMERGENCY DETECTED in lane {emergency_lane}! "
                f"Forcing green for {self.EMERGENCY_GREEN_TIME} seconds"
            )
            return SignalCommand(
                lane=emergency_lane,
                seconds=self.EMERGENCY_GREEN_TIME,
                priority=True,
                reason="Emergency vehicle detected - PRIORITY MODE"
            )
        return None

    def calculate_efficiency_metrics(self,
                                    green_time_seconds: int,
                                    avg_vehicles_waiting: int) -> Dict:
        """
        Calculate efficiency metrics including CO2 saved and wait time reduction.

        Args:
            green_time_seconds: Duration of green light
            avg_vehicles_waiting: Average vehicles waiting

        Returns:
            Dictionary with efficiency metrics
        """
        # Assumption: Without optimization, vehicles would idle for average green cycle
        # Estimate of time saved per vehicle (simplified model)
        time_saved_per_vehicle = max(0, green_time_seconds - self.MIN_GREEN_TIME) / 2
        total_time_saved = time_saved_per_vehicle * avg_vehicles_waiting
        self.total_time_saved += total_time_saved

        # CO2 calculation: 10 seconds idling = 15g CO2
        time_saved_seconds = max(0, green_time_seconds - self.MIN_GREEN_TIME)
        co2_saved = (time_saved_seconds / 10) * self.CO2_PER_10_SECONDS_IDLE * avg_vehicles_waiting
        self.co2_saved += co2_saved

        logger.info(
            f"📊 Efficiency: {total_time_saved:.1f}s saved, "
            f"{co2_saved:.1f}g CO2 prevented"
        )

        return {
            'time_saved_seconds': total_time_saved,
            'co2_saved_grams': co2_saved,
            'vehicles_affected': avg_vehicles_waiting
        }

    def check_starvation(self, traffic_state: TrafficState) -> Optional[str]:
        """
        Check if any lane is starving (hasn't had green light for 120+ seconds).
        Return the starving lane if found.

        Args:
            traffic_state: Current traffic state

        Returns:
            Starving lane name or None
        """
        now = datetime.now()
        for lane in ['N', 'S', 'E', 'W']:
            time_since_green = (now - self.lane_last_green[lane]).total_seconds()
            if time_since_green > self.STARVATION_THRESHOLD:
                logger.warning(
                    f"⚠️ STARVATION DETECTED: Lane {lane} hasn't had green in {time_since_green:.0f}s"
                )
                return lane
        return None

    def handle_deadlock(self) -> str:
        """
        Handle deadlock scenario when all lanes have 0 vehicles.
        Cycles through each lane for equal time.

        Returns:
            Lane to give green light to
        """
        self.deadlock_counter += 1
        lane_index = (self.deadlock_counter - 1) % len(self.deadlock_cycle)
        selected_lane = self.deadlock_cycle[lane_index]

        logger.info(
            f"🔄 DEADLOCK MODE: Cycling to lane {selected_lane} "
            f"({self.DEADLOCK_CYCLE_TIME}s fairness cycle)"
        )

        return selected_lane

    def optimize_signal(self, traffic_data: Dict) -> SignalCommand:
        """
        Main optimization function that determines the best signal command.
        Integrates emergency override, starvation prevention, and deadlock handling.

        Args:
            traffic_data: Dictionary with traffic state (N, S, E, W counts, emergency flag)

        Returns:
            SignalCommand with optimal signal timing
        """
        # Validate and parse traffic data
        traffic_state = TrafficState.from_dict(traffic_data)
        self.total_vehicles_processed += sum([
            traffic_state.N, traffic_state.S, traffic_state.E, traffic_state.W
        ])

        logger.info(
            f"\n🚗 Processing Traffic State: N={traffic_state.N}, S={traffic_state.S}, "
            f"E={traffic_state.E}, W={traffic_state.W}, Emergency={traffic_state.emergency}"
        )

        # 1. Check for emergency override first (highest priority)
        emergency_cmd = self.emergency_override(traffic_state)
        if emergency_cmd:
            self.lane_last_green[emergency_cmd.lane] = datetime.now()
            return emergency_cmd

        # 2. Check for starvation and prioritize starving lane
        starving_lane = self.check_starvation(traffic_state)
        if starving_lane:
            green_time = self.calculate_green_time(traffic_state, starving_lane)
            self.lane_last_green[starving_lane] = datetime.now()
            logger.info(f"🎯 Prioritizing starving lane {starving_lane}")
            return SignalCommand(
                lane=starving_lane,
                seconds=green_time,
                priority=False,
                reason=f"Starvation prevention: Lane hasn't had green in 120+ seconds"
            )

        # 3. Check for deadlock (all lanes empty)
        total_vehicles = traffic_state.N + traffic_state.S + traffic_state.E + traffic_state.W
        if total_vehicles == 0:
            deadlock_lane = self.handle_deadlock()
            self.lane_last_green[deadlock_lane] = datetime.now()
            return SignalCommand(
                lane=deadlock_lane,
                seconds=self.DEADLOCK_CYCLE_TIME,
                priority=False,
                reason="Deadlock scenario: All lanes empty, cycling for fairness"
            )
        else:
            # Reset deadlock counter when traffic resumes
            self.deadlock_counter = 0

        # 4. Normal operation: Find lane with highest density
        lane_densities = {
            'N': traffic_state.N,
            'S': traffic_state.S,
            'E': traffic_state.E,
            'W': traffic_state.W
        }

        selected_lane = max(lane_densities, key=lane_densities.get)
        vehicle_count = lane_densities[selected_lane]
        green_time = self.calculate_green_time(traffic_state, selected_lane)

        # Calculate efficiency metrics
        avg_vehicles = sum(lane_densities.values()) / 4
        self.calculate_efficiency_metrics(green_time, int(avg_vehicles))

        self.lane_last_green[selected_lane] = datetime.now()

        return SignalCommand(
            lane=selected_lane,
            seconds=green_time,
            priority=False,
            reason=f"Lane {selected_lane} has highest density ({vehicle_count} vehicles)"
        )

    def get_impact_stats(self) -> Dict:
        """
        Get cumulative impact statistics for reporting.

        Returns:
            Dictionary with impact metrics
        """
        stats = {
            'total_vehicles_processed': self.total_vehicles_processed,
            'total_time_saved_seconds': round(self.total_time_saved, 2),
            'co2_saved_grams': round(self.co2_saved, 2),
            'co2_saved_kg': round(self.co2_saved / 1000, 3)
        }
        logger.info(f"\n📈 Impact Stats: {stats}")
        return stats

    def reset_stats(self):
        """Reset impact statistics"""
        self.total_vehicles_processed = 0
        self.total_time_saved = 0
        self.co2_saved = 0
        logger.info("🔄 Statistics reset")


# Global optimizer instance
_optimizer = None


def get_optimizer() -> TrafficOptimizer:
    """Get or create the global optimizer instance (singleton pattern)"""
    global _optimizer
    if _optimizer is None:
        _optimizer = TrafficOptimizer()
    return _optimizer


def optimize(traffic_data: Dict) -> Dict:
    """
    Public interface for optimization.
    Can be called by crew.py as a tool.

    Args:
        traffic_data: Dictionary with N, S, E, W vehicle counts and emergency flag

    Returns:
        Dictionary with signal command (lane, seconds, priority, reason)
    """
    optimizer = get_optimizer()
    command = optimizer.optimize_signal(traffic_data)
    return command.model_dump()
