"""Shared SQLAlchemy column types."""
from __future__ import annotations

from sqlalchemy import Enum

from app.models.enums import LearningLevel, ProgressStatus, QuestionType, StorageProvider

learning_level_enum = Enum(LearningLevel, name="learning_level")
question_type_enum = Enum(QuestionType, name="question_type")
storage_provider_enum = Enum(StorageProvider, name="storage_provider")
lesson_progress_status_enum = Enum(ProgressStatus, name="lesson_progress_status")
