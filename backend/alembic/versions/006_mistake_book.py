"""create mistake book tables

Revision ID: 006_mistake_book
Revises: 005_math_learning_module
Create Date: 2026-10-07 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '006_mistake_book'
down_revision: Union[str, None] = '005_math_learning_module'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'mistake_book_entries',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('question_id', sa.Uuid(), nullable=False),
        sa.Column('attempt_id', sa.Uuid(), nullable=True),
        sa.Column('subject', sa.String(length=32), nullable=False),
        sa.Column('domain', sa.String(length=64), nullable=False),
        sa.Column('skill', sa.String(length=128), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='ACTIVE', nullable=False),
        sa.Column('mistake_type', sa.String(length=32), server_default='UNKNOWN', nullable=False),
        sa.Column('review_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('correct_retry_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('incorrect_retry_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_review_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['attempt_id'], ['question_attempts.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'question_id', name='uq_mistake_book_user_question'),
    )
    op.create_index('ix_mistake_book_entries_user_id', 'mistake_book_entries', ['user_id'], unique=False)
    op.create_index('ix_mistake_book_entries_question_id', 'mistake_book_entries', ['question_id'], unique=False)
    op.create_index('ix_mistake_book_entries_status', 'mistake_book_entries', ['status'], unique=False)
    op.create_index('ix_mistake_book_entries_subject', 'mistake_book_entries', ['subject'], unique=False)
    op.create_index('ix_mistake_book_entries_domain', 'mistake_book_entries', ['domain'], unique=False)
    op.create_index('ix_mistake_book_entries_skill', 'mistake_book_entries', ['skill'], unique=False)
    op.create_index('ix_mistake_book_entries_next_review_at', 'mistake_book_entries', ['next_review_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_mistake_book_entries_next_review_at', table_name='mistake_book_entries')
    op.drop_index('ix_mistake_book_entries_skill', table_name='mistake_book_entries')
    op.drop_index('ix_mistake_book_entries_domain', table_name='mistake_book_entries')
    op.drop_index('ix_mistake_book_entries_subject', table_name='mistake_book_entries')
    op.drop_index('ix_mistake_book_entries_status', table_name='mistake_book_entries')
    op.drop_index('ix_mistake_book_entries_question_id', table_name='mistake_book_entries')
    op.drop_index('ix_mistake_book_entries_user_id', table_name='mistake_book_entries')
    op.drop_table('mistake_book_entries')
