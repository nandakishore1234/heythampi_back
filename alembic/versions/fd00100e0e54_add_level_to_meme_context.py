"""add_level_to_meme_context

Revision ID: fd00100e0e54
Revises: 09687cff7b89
Create Date: 2025-11-21 12:50:50.602089

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fd00100e0e54'
down_revision: Union[str, Sequence[str], None] = '09687cff7b89'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add level column to meme_contexts table
    # The enum type should already exist from initial migration
    op.add_column(
        'meme_contexts',
        sa.Column('level', 
                  sa.Enum('beginner', 'basic', 'intermediate', 'advanced', 'fluent', 
                          name='learning_level', create_type=False), 
                  nullable=False, 
                  server_default="'beginner'::learning_level")
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove level column from meme_contexts table
    op.drop_column('meme_contexts', 'level')
