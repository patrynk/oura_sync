"""daily_activity model based on Oura API schema."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, Date, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, OuraBaseMixin

class DailyActivity(Base, OuraBaseMixin):
    __tablename__ = "daily_activity"
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Core fields
    day: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Activity metrics
    active_calories: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    average_met_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    equivalent_walking_distance: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    high_activity_met_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    high_activity_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    inactivity_alerts: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    low_activity_met_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    low_activity_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    medium_activity_met_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    medium_activity_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    meters_to_target: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    non_wear_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    resting_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sedentary_met_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sedentary_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    steps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_calories: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_meters: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_calories: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Activity classification (stored as text string)
    class_5_min: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # MET interval (stored as float for interval value)
    met_interval: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Contributors
    meet_daily_targets: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    move_every_hour: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    recovery_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    stay_active: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    training_frequency: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    training_volume: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Raw JSON data for extensibility (stores met.items array and other nested data)
    raw_data: Mapped[str] = mapped_column(Text, nullable=True)
