"""Request and response schemas for Mzima flow operations."""

from __future__ import annotations

import datetime
import uuid
from typing import Any

from pydantic import BaseModel, Field


class ObservationCreate(BaseModel):
    visit_id: uuid.UUID
    temperature_c: float | None = None
    pulse_bpm: int | None = None
    respiratory_rate: int | None = None
    oxygen_saturation: int | None = None
    capillary_refill_seconds: float | None = None
    systolic_bp: int | None = None
    diastolic_bp: int | None = None
    avpu: str | None = None
    severe_pallor: bool | None = None
    reported_symptoms: str | None = None
    symptom_summary: dict[str, Any] = Field(default_factory=dict)
    data_source: str = "synthetic"


class ClinicalAlertReviewCreate(BaseModel):
    decision: str = Field(..., description="reviewed, dismissed, escalated, or acknowledged")
    reason: str | None = None


class StationCreate(BaseModel):
    station_code: str
    name: str
    service_point: str
    zone_code: str | None = None
    functional: bool = True
    staffed: bool = True
    capacity_per_hour: int = 4
    required_role: str = "nurse"
    location_notes: str | None = None


class StationStatusUpdate(BaseModel):
    functional: bool | None = None
    staffed: bool | None = None
    capacity_per_hour: int | None = None


class StaffingCreate(BaseModel):
    shift_start: datetime.datetime
    shift_end: datetime.datetime
    role: str
    service_point: str | None = None
    planned_count: int = 0
    available_count: int = 0
    notes: str | None = None


class RecommendationReviewCreate(BaseModel):
    decision: str = Field(..., description="acknowledged, rejected, deferred, or applied_external")
    reason: str | None = None


class SimulationRequest(BaseModel):
    name: str = "what-if simulation"
    description: str | None = None
    baseline_arrivals_per_hour: float | None = None
    baseline_service_minutes: float = 15.0
    baseline_stations: int = 2
    scenario_stations: int = 3
    scenario_staff: int | None = None
    scenario_service_minutes: float | None = None
    created_by: str | None = None


class TextExtractionRequest(BaseModel):
    text: str
    visit_id: uuid.UUID | None = None


class BottleneckScanRequest(BaseModel):
    service_points: list[str | None] | None = None
