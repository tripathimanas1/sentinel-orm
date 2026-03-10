"""Action log model for PostgreSQL."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import String, Text, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.postgres import Base


class ActionLog(Base):
    """Action log for governance and audit trail."""

    __tablename__ = "action_logs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    brand_id: Mapped[UUID] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    risk_event_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    severity: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # 'low', 'medium', 'high', 'critical'
    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False, index=True
    )  # 'pending', 'in_progress', 'resolved', 'dismissed'
    assigned_to: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<ActionLog(id={self.id}, type={self.action_type}, status={self.status})>"


__table_args__ = (
    Index("idx_action_logs_brand_status", "brand_id", "status"),
    Index("idx_action_logs_brand_created", "brand_id", "created_at"),
)
