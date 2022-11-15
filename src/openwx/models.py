"""A collection of commonly data models."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from pydantic import BaseModel


class Forecast(BaseModel):
    """A pydantic model for storing individual forecasts."""

    valid_time: datetime
    parameters: Dict[str, float]


class ForecastResponseModel(BaseModel):
    """A pydantic model for formatting api responses."""

    lat: float
    lon: float
    forecasts: List[Forecast]


class Coords(BaseModel):
    """Dataclass used to store a Location."""

    latitude: float
    longitude: float
