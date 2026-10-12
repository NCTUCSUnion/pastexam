"""add archives course_id deleted_at index

Revision ID: 7c1e4b2a9d50
Revises: 01075665e961
Create Date: 2026-10-12 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '7c1e4b2a9d50'
down_revision: Union[str, Sequence[str], None] = '01075665e961'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index('ix_archives_course_id_deleted_at', 'archives', ['course_id', 'deleted_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_archives_course_id_deleted_at', table_name='archives')
