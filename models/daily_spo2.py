"""daily_spo2 model stub - expand based on API schema."""
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, OuraBaseMixin

class DailySpo2(Base, OuraBaseMixin):
    __tablename__ = "daily_spo2"
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    raw_data: Mapped[str] = mapped_column(Text, nullable=True)
