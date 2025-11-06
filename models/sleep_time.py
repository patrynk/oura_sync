"""sleep_time model stub - expand based on API schema."""
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, OuraBaseMixin

class SleepTime(Base, OuraBaseMixin):
    __tablename__ = "sleep_time"
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    raw_data: Mapped[str] = mapped_column(Text, nullable=True)
