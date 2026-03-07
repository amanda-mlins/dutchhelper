"""add_is_admin_to_users

Revision ID: 841f45df2c2a
Revises: 8ba2649068a3
Create Date: 2026-03-06 17:49:05.351692

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '841f45df2c2a'
down_revision: Union[str, Sequence[str], None] = '8ba2649068a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op: is_admin was folded into the initial_schema migration (8ba2649068a3).
    This revision is kept to preserve the migration chain for existing dev databases
    that were stamped before the initial migration was backfilled.
    """
    pass


def downgrade() -> None:
    """No-op: see upgrade() note above."""
    pass
