"""daily_spo2 model based on Oura API schema."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, Date, Float
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, OuraBaseMixin

class DailySpo2(Base, OuraBaseMixin):
    __tablename__ = "daily_spo2"
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Core fields
    day: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    breathing_disturbance_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    spo2_percentage_average: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Raw JSON data for extensibility
    raw_data: Mapped[str] = mapped_column(Text, nullable=True)
