"""
Traffic Logic Module

This package contains the optimization logic for traffic signal control.
"""

from .optimizer import (
    TrafficOptimizer,
    TrafficState,
    SignalCommand,
    LaneMetrics,
    get_optimizer,
    optimize
)

__all__ = [
    'TrafficOptimizer',
    'TrafficState',
    'SignalCommand',
    'LaneMetrics',
    'get_optimizer',
    'optimize'
]
