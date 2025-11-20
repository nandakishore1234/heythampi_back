"""Content hierarchy models (sections, units, lessons)."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import LearningLevel
from app.models.mixins import TimestampMixin
from app.models.types import learning_level_enum

if TYPE_CHECKING:
    from app.models.meme import MemeContext
    from app.models.quiz import QuizQuestion
    from app.models.user import UserLessonProgress
    from app.models.tag import Tag


class Section(TimestampMixin, Base):
    __tablename__ = "sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    units: Mapped[list["Unit"]] = relationship(back_populates="section", cascade="all, delete-orphan")


class Unit(TimestampMixin, Base):
    __tablename__ = "units"

    __table_args__ = (
        UniqueConstraint("section_id", "order_index", name="uq_unit_order"),
        UniqueConstraint("section_id", "slug", name="uq_unit_slug"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    section_id: Mapped[int] = mapped_column(ForeignKey("sections.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    section: Mapped[Section] = relationship(back_populates="units")
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="unit", cascade="all, delete-orphan")


class Lesson(TimestampMixin, Base):
    __tablename__ = "lessons"

    __table_args__ = (
        UniqueConstraint("unit_id", "order_index", name="uq_lesson_order"),
        UniqueConstraint("unit_id", "slug", name="uq_lesson_slug"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    level: Mapped[LearningLevel] = mapped_column(learning_level_enum.copy(), nullable=False)
    xp_reward: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    estimated_duration_minutes: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    unit: Mapped[Unit] = relationship(back_populates="lessons")
    meme_contexts: Mapped[list["MemeContext"]] = relationship(back_populates="lesson", cascade="all, delete-orphan")
    quiz_questions: Mapped[list["QuizQuestion"]] = relationship(back_populates="lesson", cascade="all, delete-orphan")
    progress_records: Mapped[list["UserLessonProgress"]] = relationship(back_populates="lesson", cascade="all, delete-orphan")
    tags: Mapped[list["Tag"]] = relationship("Tag", secondary="lesson_tags", back_populates="lessons")
