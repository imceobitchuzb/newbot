"""create math learning module tables

Revision ID: 005_math_learning_module
Revises: 004_diagnostic_module
Create Date: 2026-10-07 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '005_math_learning_module'
down_revision: Union[str, None] = '004_diagnostic_module'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Math Practice Sessions table
    op.create_table(
        'math_practice_sessions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('domain', sa.String(length=64), nullable=True),
        sa.Column('difficulty', sa.String(length=16), nullable=True),
        sa.Column('skill', sa.String(length=128), nullable=True),
        sa.Column('total_questions', sa.Integer(), server_default='10', nullable=False),
        sa.Column('current_question_index', sa.Integer(), server_default='0', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='IN_PROGRESS', nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_math_practice_sessions_user_id', 'math_practice_sessions', ['user_id'], unique=False)
    op.create_index('ix_math_practice_sessions_status', 'math_practice_sessions', ['status'], unique=False)
    op.create_index('ix_math_practice_sessions_domain', 'math_practice_sessions', ['domain'], unique=False)

    # 2. Math Practice Questions table
    op.create_table(
        'math_practice_questions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('session_id', sa.Uuid(), nullable=False),
        sa.Column('question_id', sa.Uuid(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('selected_option_id', sa.Uuid(), nullable=True),
        sa.Column('attempt_id', sa.Uuid(), nullable=True),
        sa.Column('is_answered', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('time_spent_seconds', sa.Integer(), server_default='0', nullable=False),
        sa.Column('answered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['math_practice_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['selected_option_id'], ['question_options.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['attempt_id'], ['question_attempts.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'order_index', name='uq_math_practice_questions_session_order'),
        sa.UniqueConstraint('session_id', 'question_id', name='uq_math_practice_questions_session_question'),
    )
    op.create_index('ix_math_practice_questions_session_id', 'math_practice_questions', ['session_id'], unique=False)
    op.create_index('ix_math_practice_questions_question_id', 'math_practice_questions', ['question_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_math_practice_questions_question_id', table_name='math_practice_questions')
    op.drop_index('ix_math_practice_questions_session_id', table_name='math_practice_questions')
    op.drop_table('math_practice_questions')

    op.drop_index('ix_math_practice_sessions_domain', table_name='math_practice_sessions')
    op.drop_index('ix_math_practice_sessions_status', table_name='math_practice_sessions')
    op.drop_index('ix_math_practice_sessions_user_id', table_name='math_practice_sessions')
    op.drop_table('math_practice_sessions')
