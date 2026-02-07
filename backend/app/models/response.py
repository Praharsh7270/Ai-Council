"""Response model."""
from datetime import datetime
from typing import Any, Dict
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Response(Base):
    """Response model for AI Council outputs."""

    __tablename__ = "responses"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    request_id: Mapped[UUID] = mapped_column(
        ForeignKey("requests.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False)
    execution_time: Mapped[float] = mapped_column(Float, nullable=False)
    models_used: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    orchestration_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    # Relationships
    request: Mapped["Request"] = relationship("Request", back_populates="response")

    def __repr__(self) -> str:
        return f"<Response(id={self.id}, request_id={self.request_id}, confidence={self.confidence})>"
