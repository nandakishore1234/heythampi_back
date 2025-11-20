"""Quiz question and answer models."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import LearningLevel, QuestionType
from app.models.mixins import TimestampMixin
from app.models.types import learning_level_enum, question_type_enum

if TYPE_CHECKING:
    from app.models.content import Lesson
    from app.models.meme import MemeContext
    from app.models.user import UserQuizAttempt
    from app.models.tag import Tag


class QuizQuestion(TimestampMixin, Base):
    __tablename__ = "quiz_questions"

    __table_args__ = (
        UniqueConstraint("lesson_id", "order_index", name="uq_question_order"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    meme_context_id: Mapped[int | None] = mapped_column(ForeignKey("meme_contexts.id", ondelete="SET NULL"))
    question_type: Mapped[QuestionType] = mapped_column(question_type_enum.copy(), nullable=False)
    prompt_ml: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_en: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty_level: Mapped[LearningLevel] = mapped_column(learning_level_enum.copy(), nullable=False)
    hint_ml: Mapped[str | None] = mapped_column(Text)
    hint_en: Mapped[str | None] = mapped_column(Text)
    explanation_ml: Mapped[str | None] = mapped_column(Text)
    explanation_en: Mapped[str | None] = mapped_column(Text)
    xp_value: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    time_limit_seconds: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    lesson: Mapped["Lesson"] = relationship(back_populates="quiz_questions")
    meme_context: Mapped["MemeContext | None"] = relationship(back_populates="quiz_questions")
    answers: Mapped[list["QuizAnswer"]] = relationship(back_populates="question", cascade="all, delete-orphan")
    attempts: Mapped[list["UserQuizAttempt"]] = relationship(back_populates="question", cascade="all, delete-orphan")
    tags: Mapped[list["Tag"]] = relationship("Tag", secondary="quiz_question_tags", back_populates="quiz_questions")


class QuizAnswer(TimestampMixin, Base):
    __tablename__ = "quiz_answers"

    __table_args__ = (
        UniqueConstraint("question_id", "order_index", name="uq_answer_order"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False)
    answer_text_ml: Mapped[str] = mapped_column(Text, nullable=False)
    answer_text_en: Mapped[str] = mapped_column(Text, nullable=False)
    answer_media_path: Mapped[str | None] = mapped_column(String(512))
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    feedback_ml: Mapped[str | None] = mapped_column(Text)
    feedback_en: Mapped[str | None] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    question: Mapped[QuizQuestion] = relationship(back_populates="answers")
