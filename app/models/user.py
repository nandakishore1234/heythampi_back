"""User and gamification-related models."""
from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import LearningLevel, ProgressStatus
from app.models.types import learning_level_enum, lesson_progress_status_enum
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.content import Lesson
    from app.models.quiz import QuizQuestion


class User(TimestampMixin, Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    is_superuser: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    total_xp: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    current_level: Mapped[LearningLevel] = mapped_column(
        learning_level_enum.copy(),
        nullable=False,
        default=LearningLevel.beginner,
    )
    streak_current: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    streak_longest: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    profile: Mapped["UserProfile"] = relationship(back_populates="user", uselist=False)
    lesson_progress: Mapped[list["UserLessonProgress"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    quiz_attempts: Mapped[list["UserQuizAttempt"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    badges: Mapped[list["UserBadge"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    streaks: Mapped[list["UserStreak"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserProfile(TimestampMixin, Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    display_language: Mapped[str] = mapped_column(String(10), nullable=False, server_default="en")
    locale: Mapped[str | None] = mapped_column(String(20))
    avatar_url: Mapped[str | None] = mapped_column(String(512))

    user: Mapped[User] = relationship(back_populates="profile")


class Badge(TimestampMixin, Base):
    __tablename__ = "badges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(String(512))
    icon_path: Mapped[str | None] = mapped_column(String(512))
    xp_reward: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    users: Mapped[list["UserBadge"]] = relationship(back_populates="badge")


class UserBadge(TimestampMixin, Base):
    __tablename__ = "user_badges"

    __table_args__ = (UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    badge_id: Mapped[int] = mapped_column(ForeignKey("badges.id", ondelete="CASCADE"), nullable=False)
    awarded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default="now()")
    notes: Mapped[str | None] = mapped_column(String(512))

    user: Mapped[User] = relationship(back_populates="badges")
    badge: Mapped[Badge] = relationship(back_populates="users")


class UserStreak(TimestampMixin, Base):
    __tablename__ = "user_streaks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    streak_start: Mapped[date] = mapped_column(Date, nullable=False)
    streak_end: Mapped[date | None] = mapped_column(Date)
    streak_length: Mapped[int] = mapped_column(Integer, nullable=False)

    user: Mapped[User] = relationship(back_populates="streaks")


class UserLessonProgress(TimestampMixin, Base):
    __tablename__ = "user_lesson_progress"

    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    progress_status: Mapped[ProgressStatus] = mapped_column(
        lesson_progress_status_enum.copy(),
        nullable=False,
        default=ProgressStatus.not_started,
    )
    xp_earned: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    last_interaction_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="lesson_progress")
    lesson: Mapped["Lesson"] = relationship(back_populates="progress_records")


class UserQuizAttempt(TimestampMixin, Base):
    __tablename__ = "user_quiz_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False)
    selected_answer_ids: Mapped[list[int] | None] = mapped_column(
        ARRAY(Integer),
        nullable=True,
    )
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    time_spent_ms: Mapped[int | None] = mapped_column(Integer)
    free_text_answer: Mapped[str | None] = mapped_column(Text)

    user: Mapped[User] = relationship(back_populates="quiz_attempts")
    question: Mapped["QuizQuestion"] = relationship(back_populates="attempts")
