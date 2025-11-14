"""daily_stress model based on Oura API schema."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, Date
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, OuraBaseMixin

class DailyStress(Base, OuraBaseMixin):
    __tablename__ = "daily_stress"
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Core fields
    day: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    day_summary: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    recovery_high: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    stress_high: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Raw JSON data for extensibility
    raw_data: Mapped[str] = mapped_column(Text, nullable=True)
