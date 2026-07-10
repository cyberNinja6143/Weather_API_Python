"""Response model for the hottest-day query."""

import datetime as _dt
from typing import Optional

from pydantic import BaseModel, Field


class HottestDayResponse(BaseModel):
    city: str = Field(..., description="City name as stored.")
    date: _dt.date = Field(..., description="Date of the hottest day.")
    temperature_2m_max: Optional[float] = Field(None, description="Maximum temperature on that day.")
