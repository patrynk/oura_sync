"""daily_sleep model based on Oura API schema."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, DateTime, Date
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, OuraBaseMixin

class DailySleep(Base, OuraBaseMixin):
    __tablename__ = "daily_sleep"
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Core fields
    day: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Contributors
    deep_sleep: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    efficiency: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    latency: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rem_sleep: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    restfulness: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    timing: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_sleep: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Raw JSON data for extensibility
    raw_data: Mapped[str] = mapped_column(Text, nullable=True)
