"""encrypt gemini api keys

Revision ID: b2f6c1d8e4a7
Revises: 7c1e4b2a9d50
Create Date: 2026-10-12 20:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.utils.crypto import ENCRYPTED_PREFIX, decrypt_secret, encrypt_secret

# revision identifiers, used by Alembic.
revision: str = 'b2f6c1d8e4a7'
down_revision: str | Sequence[str] | None = '7c1e4b2a9d50'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Encrypt API keys that were stored in plaintext."""
    conn = op.get_bind()
    # A cleared key was sometimes stored as an empty string
    conn.execute(sa.text("UPDATE users SET gemini_api_key = NULL WHERE gemini_api_key = ''"))
    rows = conn.execute(
        sa.text(
            "SELECT id, gemini_api_key FROM users "
            "WHERE gemini_api_key IS NOT NULL AND gemini_api_key NOT LIKE :prefix"
        ),
        {"prefix": f"{ENCRYPTED_PREFIX}%"},
    ).all()
    for user_id, api_key in rows:
        conn.execute(
            sa.text("UPDATE users SET gemini_api_key = :key WHERE id = :id"),
            {"key": encrypt_secret(api_key), "id": user_id},
        )


def downgrade() -> None:
    """Store API keys in plaintext again."""
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT id, gemini_api_key FROM users WHERE gemini_api_key LIKE :prefix"
        ),
        {"prefix": f"{ENCRYPTED_PREFIX}%"},
    ).all()
    for user_id, api_key in rows:
        conn.execute(
            sa.text("UPDATE users SET gemini_api_key = :key WHERE id = :id"),
            {"key": decrypt_secret(api_key), "id": user_id},
        )
