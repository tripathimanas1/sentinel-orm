"""Source model for PostgreSQL."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import String, Boolean, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.postgres import Base


class Source(Base):
    """Signal source configuration."""

    __tablename__ = "sources"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    brand_id: Mapped[UUID] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # 'review', 'social', 'ticket', 'news', 'influencer'
    platform: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )  # 'google', 'twitter', 'reddit', etc.
    source_identifier: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Source(id={self.id}, type={self.source_type}, platform={self.platform})>"


__table_args__ = (
    Index("idx_sources_brand_type", "brand_id", "source_type"),
    Index("idx_sources_brand_platform", "brand_id", "platform"),
)
