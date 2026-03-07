"""initial_schema

Revision ID: 8ba2649068a3
Revises: 
Create Date: 2026-03-06 17:40:48.712292

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8ba2649068a3'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('hashed_password', sa.String(), nullable=True),
        sa.Column('google_id', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_id', 'users', ['id'], unique=False)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_google_id', 'users', ['google_id'], unique=True)

    op.create_table(
        'user_words',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('word', sa.String(), nullable=False),
        sa.Column('word_type', sa.String(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_practiced_at', sa.DateTime(), nullable=True),
        sa.Column('practice_count', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_user_words_id', 'user_words', ['id'], unique=False)
    op.create_index('ix_user_words_word', 'user_words', ['word'], unique=False)
    op.create_index('ix_user_words_word_type', 'user_words', ['word_type'], unique=False)

    op.create_table(
        'article_game_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('played_at', sa.DateTime(), nullable=False),
        sa.Column('word_count', sa.Integer(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('accuracy', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_article_game_sessions_id', 'article_game_sessions', ['id'], unique=False)

    op.create_table(
        'article_game_answers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), sa.ForeignKey('article_game_sessions.id'), nullable=False),
        sa.Column('word', sa.String(), nullable=False),
        sa.Column('correct_article', sa.String(), nullable=False),
        sa.Column('user_answer', sa.String(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_article_game_answers_id', 'article_game_answers', ['id'], unique=False)

    op.create_table(
        'article_word_mistakes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('word', sa.String(), nullable=False),
        sa.Column('times_seen', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('times_wrong', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_seen_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_article_word_mistakes_id', 'article_word_mistakes', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('article_word_mistakes')
    op.drop_table('article_game_answers')
    op.drop_table('article_game_sessions')
    op.drop_table('user_words')
    op.drop_table('users')
