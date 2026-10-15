"""Deterministic operational simulation for Mzima.

This estimates the effect of staffing and station changes without mutating queue state.
"""

from __future__ import annotations

import math
from typing import Any

from app.services.flow.capacity import available_staff_count, effective_capacity_per_hour


def _steady_state_wait(arrivals_per_hour: float, service_minutes: float, stations: int) -> tuple[float, float, float]:
    throughput_per_hour = (stations * 60.0 / service_minutes) if service_minutes > 0 and stations > 0 else 0.0
    utilisation = (arrivals_per_hour / throughput_per_hour) if throughput_per_hour > 0 else 999.0
    if utilisation >= 0.98:
        estimated_wait = 999.0
        queue_size = 999.0
    else:
        estimated_wait = (utilisation / max(1.0 - utilisation, 0.01)) * service_minutes
        queue_size = utilisation / max(1.0 - utilisation, 0.01)
    return round(throughput_per_hour, 2), round(utilisation, 3), round(estimated_wait, 2), round(queue_size, 2)


def simulate_capacity_scenario(
    baseline_arrivals_per_hour: float,
    baseline_service_minutes: float,
    baseline_stations: int,
    scenario_stations: int,
    scenario_staff: int | None = None,
    scenario_service_minutes: float | None = None,
) -> dict[str, Any]:
    scenario_service_minutes = scenario_service_minutes or baseline_service_minutes
    baseline_throughput, baseline_utilisation, baseline_wait, baseline_queue = _steady_state_wait(
        baseline_arrivals_per_hour,
        baseline_service_minutes,
        baseline_stations,
    )
    effective_stations = baseline_stations
    if scenario_staff is not None:
        effective_stations = min(scenario_stations, scenario_staff)
    effective_stations = max(1, effective_stations)
    scenario_throughput, scenario_utilisation, scenario_wait, scenario_queue = _steady_state_wait(
        baseline_arrivals_per_hour,
        scenario_service_minutes,
        effective_stations,
    )
    return {
        "baseline": {
            "arrivals_per_hour": baseline_arrivals_per_hour,
            "service_minutes": baseline_service_minutes,
            "stations": baseline_stations,
            "throughput_per_hour": baseline_throughput,
            "utilisation": baseline_utilisation,
            "estimated_wait_minutes": baseline_wait,
            "estimated_queue_size": baseline_queue,
        },
        "scenario": {
            "arrivals_per_hour": baseline_arrivals_per_hour,
            "service_minutes": scenario_service_minutes,
            "stations": effective_stations,
            "throughput_per_hour": scenario_throughput,
            "utilisation": scenario_utilisation,
            "estimated_wait_minutes": scenario_wait,
            "estimated_queue_size": scenario_queue,
        },
        "projected_wait_reduction_minutes": round(max(0.0, baseline_wait - scenario_wait), 2),
        "projected_queue_reduction": max(0, int(baseline_queue - scenario_queue)) if baseline_queue < 999 else None,
        "safety_warning": scenario_utilisation >= 0.95,
        "assumptions": {
            "steady_state_approximation": True,
            "observed_arrival_rate_used": True,
            "no_queue_state_mutated": True,
        },
    }
