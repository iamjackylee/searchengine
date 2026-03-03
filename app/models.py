from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    articles: Mapped[list["Article"]] = relationship(back_populates="source")


class Article(Base):
    __tablename__ = "articles"
    __table_args__ = (UniqueConstraint("canonical_url", name="uq_articles_canonical_url"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    snippet: Mapped[str] = mapped_column(Text, default="", nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    canonical_url: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    source: Mapped[Source] = relationship(back_populates="articles")
