"""Meme context and media models."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import StorageProvider
from app.models.mixins import TimestampMixin
from app.models.types import storage_provider_enum

if TYPE_CHECKING:
    from app.models.content import Lesson
    from app.models.quiz import QuizQuestion
    from app.models.tag import Tag


class MemeContext(TimestampMixin, Base):
    __tablename__ = "meme_contexts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    context_title: Mapped[str | None] = mapped_column(String(150))
    context_text_ml: Mapped[str] = mapped_column(Text, nullable=False)
    context_text_en: Mapped[str] = mapped_column(Text, nullable=False)
    explanation_notes: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(String(512))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    lesson: Mapped["Lesson"] = relationship(back_populates="meme_contexts")
    media_assets: Mapped[list["MemeMedia"]] = relationship(back_populates="meme_context", cascade="all, delete-orphan")
    quiz_questions: Mapped[list["QuizQuestion"]] = relationship(back_populates="meme_context")
    tags: Mapped[list["Tag"]] = relationship("Tag", secondary="meme_context_tags", back_populates="meme_contexts")


class MemeMedia(TimestampMixin, Base):
    __tablename__ = "meme_media"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    meme_context_id: Mapped[int] = mapped_column(ForeignKey("meme_contexts.id", ondelete="CASCADE"), nullable=False)
    storage_provider: Mapped[StorageProvider] = mapped_column(storage_provider_enum.copy(), nullable=False)
    remote_path: Mapped[str] = mapped_column(String(512), nullable=False)
    thumbnail_path: Mapped[str | None] = mapped_column(String(512))
    content_hash: Mapped[str | None] = mapped_column(String(128))
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    meme_context: Mapped[MemeContext] = relationship(back_populates="media_assets")
