"""OAuth token storage model."""
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class OAuthToken(Base, TimestampMixin):
    """Store OAuth tokens for Oura API access."""
    
    __tablename__ = "oauth_tokens"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # User identification
    user_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    
    # OAuth tokens
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    token_type: Mapped[str] = mapped_column(String(50), default="Bearer")
    
    # Token expiry
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Scopes granted
    scopes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    def is_expired(self) -> bool:
        """Check if access token is expired."""
        if not self.expires_at:
            return False
        return datetime.now(self.expires_at.tzinfo) >= self.expires_at
    
    def __repr__(self) -> str:
        return f"<OAuthToken(user_id='{self.user_id}', expires_at='{self.expires_at}')>"