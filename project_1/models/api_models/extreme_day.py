"""Model for an individual extreme-heat day."""

import datetime as _dt
from typing import Optional

from pydantic import BaseModel, Field


class ExtremeDay(BaseModel):
    date: _dt.date = Field(..., description="Date of the extreme heat day.")
    temperature_2m_max: Optional[float] = Field(None, description="Max temperature that day.")
