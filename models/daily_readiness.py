"""daily_readiness model based on Oura API schema."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, DateTime, Date, Float
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, OuraBaseMixin

class DailyReadiness(Base, OuraBaseMixin):
    __tablename__ = "daily_readiness"
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Core fields
    day: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    temperature_deviation: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    temperature_trend_deviation: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Contributors
    activity_balance: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    body_temperature: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    hrv_balance: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    previous_day_activity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    previous_night: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    recovery_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    resting_heart_rate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sleep_balance: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sleep_regularity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Raw JSON data for extensibility
    raw_data: Mapped[str] = mapped_column(Text, nullable=True)
