"""create initial schema

Revision ID: 09687cff7b89
Revises: 
Create Date: 2025-11-10 16:19:18.161116

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '09687cff7b89'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


LEARNING_LEVEL_VALUES = ("beginner", "basic", "intermediate", "advanced", "fluent")
QUESTION_TYPE_VALUES = (
    "multiple_choice_single",
    "multiple_choice_multi",
    "true_false",
    "text_input",
    "ordering",
)
STORAGE_PROVIDER_VALUES = ("firebase", "s3", "local")
LESSON_PROGRESS_STATUS_VALUES = ("NOT_STARTED", "IN_PROGRESS", "COMPLETED")

learning_level_enum = postgresql.ENUM(*LEARNING_LEVEL_VALUES, name="learning_level", create_type=True)
question_type_enum = postgresql.ENUM(*QUESTION_TYPE_VALUES, name="question_type", create_type=True)
storage_provider_enum = postgresql.ENUM(*STORAGE_PROVIDER_VALUES, name="storage_provider", create_type=True)
lesson_progress_status_enum = postgresql.ENUM(
    *LESSON_PROGRESS_STATUS_VALUES,
    name="lesson_progress_status",
    create_type=True,
)


def learning_level_type() -> sa.Enum:
    return postgresql.ENUM(*LEARNING_LEVEL_VALUES, name="learning_level", create_type=False)


def question_type() -> sa.Enum:
    return postgresql.ENUM(*QUESTION_TYPE_VALUES, name="question_type", create_type=False)


def storage_provider_type() -> sa.Enum:
    return postgresql.ENUM(*STORAGE_PROVIDER_VALUES, name="storage_provider", create_type=False)


def lesson_progress_status_type() -> sa.Enum:
    return postgresql.ENUM(
        *LESSON_PROGRESS_STATUS_VALUES,
        name="lesson_progress_status",
        create_type=False,
    )


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()

    learning_level_enum.create(bind, checkfirst=True)
    question_type_enum.create(bind, checkfirst=True)
    storage_provider_enum.create(bind, checkfirst=True)
    lesson_progress_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "sections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=160), nullable=False, unique=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "units",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("section_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["section_id"], ["sections.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("section_id", "order_index", name="uq_unit_order"),
        sa.UniqueConstraint("section_id", "slug", name="uq_unit_slug"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("username", sa.String(length=50), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("total_xp", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("current_level", learning_level_type(), nullable=False, server_default=sa.text("'beginner'::learning_level")),
        sa.Column("streak_current", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("streak_longest", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "badges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=100), nullable=False, unique=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.String(length=512), nullable=True),
        sa.Column("icon_path", sa.String(length=512), nullable=True),
        sa.Column("xp_reward", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "lessons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("unit_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("level", learning_level_type(), nullable=False),
        sa.Column("xp_reward", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("estimated_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("unit_id", "order_index", name="uq_lesson_order"),
        sa.UniqueConstraint("unit_id", "slug", name="uq_lesson_slug"),
    )

    op.create_table(
        "user_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("display_language", sa.String(length=10), nullable=False, server_default="en"),
        sa.Column("locale", sa.String(length=20), nullable=True),
        sa.Column("avatar_url", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "meme_contexts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lesson_id", sa.Integer(), nullable=False),
        sa.Column("context_title", sa.String(length=150), nullable=True),
        sa.Column("context_text_ml", sa.Text(), nullable=False),
        sa.Column("context_text_en", sa.Text(), nullable=False),
        sa.Column("explanation_notes", sa.Text(), nullable=True),
        sa.Column("source_url", sa.String(length=512), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "quiz_questions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lesson_id", sa.Integer(), nullable=False),
        sa.Column("meme_context_id", sa.Integer(), nullable=True),
        sa.Column("question_type", question_type(), nullable=False),
        sa.Column("prompt_ml", sa.Text(), nullable=False),
        sa.Column("prompt_en", sa.Text(), nullable=False),
        sa.Column("difficulty_level", learning_level_type(), nullable=False),
        sa.Column("hint_ml", sa.Text(), nullable=True),
        sa.Column("hint_en", sa.Text(), nullable=True),
        sa.Column("explanation_ml", sa.Text(), nullable=True),
        sa.Column("explanation_en", sa.Text(), nullable=True),
        sa.Column("xp_value", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("time_limit_seconds", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["meme_context_id"], ["meme_contexts.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("lesson_id", "order_index", name="uq_question_order"),
    )

    op.create_table(
        "lesson_tags",
        sa.Column("lesson_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("lesson_id", "tag_id"),
        sa.UniqueConstraint("lesson_id", "tag_id", name="uq_lesson_tag"),
    )

    op.create_table(
        "meme_media",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("meme_context_id", sa.Integer(), nullable=False),
        sa.Column("storage_provider", storage_provider_type(), nullable=False),
        sa.Column("remote_path", sa.String(length=512), nullable=False),
        sa.Column("thumbnail_path", sa.String(length=512), nullable=True),
        sa.Column("content_hash", sa.String(length=128), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["meme_context_id"], ["meme_contexts.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "meme_context_tags",
        sa.Column("meme_context_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["meme_context_id"], ["meme_contexts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("meme_context_id", "tag_id"),
        sa.UniqueConstraint("meme_context_id", "tag_id", name="uq_meme_context_tag"),
    )

    op.create_table(
        "quiz_answers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("answer_text_ml", sa.Text(), nullable=False),
        sa.Column("answer_text_en", sa.Text(), nullable=False),
        sa.Column("answer_media_path", sa.String(length=512), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("feedback_ml", sa.Text(), nullable=True),
        sa.Column("feedback_en", sa.Text(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["question_id"], ["quiz_questions.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("question_id", "order_index", name="uq_answer_order"),
    )

    op.create_table(
        "quiz_question_tags",
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["question_id"], ["quiz_questions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("question_id", "tag_id"),
        sa.UniqueConstraint("question_id", "tag_id", name="uq_quiz_question_tag"),
    )

    op.create_table(
        "user_badges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("badge_id", sa.Integer(), nullable=False),
        sa.Column("awarded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("notes", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["badge_id"], ["badges.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),
    )

    op.create_table(
        "user_streaks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("streak_start", sa.Date(), nullable=False),
        sa.Column("streak_end", sa.Date(), nullable=True),
        sa.Column("streak_length", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "user_lesson_progress",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("lesson_id", sa.Integer(), nullable=False),
        sa.Column("progress_status", lesson_progress_status_type(), nullable=False, server_default=sa.text("'NOT_STARTED'::lesson_progress_status")),
        sa.Column("xp_earned", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_interaction_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson"),
    )

    op.create_table(
        "user_quiz_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("selected_answer_ids", postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("time_spent_ms", sa.Integer(), nullable=True),
        sa.Column("free_text_answer", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["question_id"], ["quiz_questions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "content_audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("before_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("after_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()

    op.drop_table("content_audit_logs")
    op.drop_table("user_quiz_attempts")
    op.drop_table("user_lesson_progress")
    op.drop_table("user_streaks")
    op.drop_table("user_badges")
    op.drop_table("quiz_question_tags")
    op.drop_table("quiz_answers")
    op.drop_table("meme_context_tags")
    op.drop_table("meme_media")
    op.drop_table("lesson_tags")
    op.drop_table("quiz_questions")
    op.drop_table("meme_contexts")
    op.drop_table("user_profiles")
    op.drop_table("lessons")
    op.drop_table("badges")
    op.drop_table("users")
    op.drop_table("units")
    op.drop_table("tags")
    op.drop_table("sections")

    lesson_progress_status_enum.drop(bind, checkfirst=True)
    storage_provider_enum.drop(bind, checkfirst=True)
    question_type_enum.drop(bind, checkfirst=True)
    learning_level_enum.drop(bind, checkfirst=True)
