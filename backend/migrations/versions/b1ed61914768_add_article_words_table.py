"""add_article_words_table

Revision ID: b1ed61914768
Revises: edf0e7a66587
Create Date: 2026-03-09 10:54:06.134884

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1ed61914768'
down_revision: Union[str, Sequence[str], None] = 'edf0e7a66587'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'article_words',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('word', sa.String(), nullable=False),
        sa.Column('article', sa.String(), nullable=False),
        sa.Column('translation', sa.String(), nullable=True),
        sa.Column('difficulty', sa.String(), nullable=False, server_default='medium'),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_article_words_id'), 'article_words', ['id'], unique=False)
    op.create_index(op.f('ix_article_words_word'), 'article_words', ['word'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_article_words_word'), table_name='article_words')
    op.drop_index(op.f('ix_article_words_id'), table_name='article_words')
    op.drop_table('article_words')
