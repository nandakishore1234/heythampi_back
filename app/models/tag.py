"""Tagging models for content categorisation."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, Table, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.content import Lesson
    from app.models.meme import MemeContext
    from app.models.quiz import QuizQuestion


class Tag(TimestampMixin, Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    lessons: Mapped[list["Lesson"]] = relationship(
        "Lesson",
        secondary="lesson_tags",
        back_populates="tags",
    )
    meme_contexts: Mapped[list["MemeContext"]] = relationship(
        "MemeContext",
        secondary="meme_context_tags",
        back_populates="tags",
    )
    quiz_questions: Mapped[list["QuizQuestion"]] = relationship(
        "QuizQuestion",
        secondary="quiz_question_tags",
        back_populates="tags",
    )


lesson_tags = Table(
    "lesson_tags",
    Base.metadata,
    Column("lesson_id", ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    UniqueConstraint("lesson_id", "tag_id", name="uq_lesson_tag"),
)


meme_context_tags = Table(
    "meme_context_tags",
    Base.metadata,
    Column("meme_context_id", ForeignKey("meme_contexts.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    UniqueConstraint("meme_context_id", "tag_id", name="uq_meme_context_tag"),
)


quiz_question_tags = Table(
    "quiz_question_tags",
    Base.metadata,
    Column("question_id", ForeignKey("quiz_questions.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    UniqueConstraint("question_id", "tag_id", name="uq_quiz_question_tag"),
)
