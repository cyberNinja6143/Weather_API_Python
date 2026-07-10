"""Weather table for Phoenix — 2025 daily records."""

from sqlalchemy import Column, Date, Float, Index

from models.db_models.base import Base


class WeatherPhoenix(Base):
    __tablename__ = "weather_phoenix"

    date = Column(Date, primary_key=True)
    temperature_2m_max = Column(Float, nullable=True)
    temperature_2m_min = Column(Float, nullable=True)
    temperature_2m_mean = Column(Float, nullable=True)
    precipitation_sum = Column(Float, nullable=True)
    wind_speed_10m_max = Column(Float, nullable=True)

    __table_args__ = (Index("ix_phx_date", "date"),)
