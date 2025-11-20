"""Enum definitions for the HeyThambi domain."""
from __future__ import annotations

import enum


class LearningLevel(str, enum.Enum):
    beginner = "beginner"
    basic = "basic"
    intermediate = "intermediate"
    advanced = "advanced"
    fluent = "fluent"


class QuestionType(str, enum.Enum):
    multiple_choice_single = "multiple_choice_single"
    multiple_choice_multi = "multiple_choice_multi"
    true_false = "true_false"
    text_input = "text_input"
    ordering = "ordering"


class StorageProvider(str, enum.Enum):
    firebase = "firebase"
    s3 = "s3"
    local = "local"


class ProgressStatus(str, enum.Enum):
    not_started = "NOT_STARTED"
    in_progress = "IN_PROGRESS"
    completed = "COMPLETED"
