"""Pydantic schemas for /health/ probes."""

from __future__ import annotations

from pydantic import BaseModel


class HealthChecks(BaseModel):
    database: bool
    storage: bool
    queue: bool


class LivenessResponse(BaseModel):
    status: str = "ok"


class ReadinessResponse(BaseModel):
    status: str
    checks: HealthChecks
