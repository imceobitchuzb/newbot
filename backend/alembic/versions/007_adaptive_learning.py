"""create adaptive learning tables

Revision ID: 007_adaptive_learning
Revises: 006_mistake_book
Create Date: 2026-10-07 20:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '007_adaptive_learning'
down_revision: Union[str, None] = '006_mistake_book'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. adaptive_profiles
    op.create_table(
        'adaptive_profiles',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('subject', sa.String(length=32), server_default='MATH', nullable=False),
        sa.Column('current_difficulty', sa.String(length=16), server_default='MEDIUM', nullable=False),
        sa.Column('total_questions', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_correct', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_active_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'subject', name='uq_adaptive_profile_user_subject'),
    )
    op.create_index('ix_adaptive_profiles_user_id', 'adaptive_profiles', ['user_id'], unique=False)
    op.create_index('ix_adaptive_profiles_subject', 'adaptive_profiles', ['subject'], unique=False)

    # 2. adaptive_practice_sessions
    op.create_table(
        'adaptive_practice_sessions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('subject', sa.String(length=32), server_default='MATH', nullable=False),
        sa.Column('current_question_index', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_questions', sa.Integer(), server_default='10', nullable=False),
        sa.Column('current_difficulty', sa.String(length=16), server_default='MEDIUM', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='IN_PROGRESS', nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_adaptive_practice_sessions_user_id', 'adaptive_practice_sessions', ['user_id'], unique=False)
    op.create_index('ix_adaptive_practice_sessions_status', 'adaptive_practice_sessions', ['status'], unique=False)

    # 3. adaptive_practice_questions
    op.create_table(
        'adaptive_practice_questions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('session_id', sa.Uuid(), nullable=False),
        sa.Column('question_id', sa.Uuid(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('difficulty_at_assignment', sa.String(length=16), server_default='MEDIUM', nullable=False),
        sa.Column('recommendation_type', sa.String(length=64), server_default='WEAK_SKILL', nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('is_answered', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('selected_option_id', sa.Uuid(), nullable=True),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('time_spent_seconds', sa.Integer(), server_default='0', nullable=False),
        sa.Column('answered_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['adaptive_practice_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['selected_option_id'], ['question_options.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'order_index', name='uq_adaptive_session_order'),
        sa.UniqueConstraint('session_id', 'question_id', name='uq_adaptive_session_question'),
    )
    op.create_index('ix_adaptive_practice_questions_session_id', 'adaptive_practice_questions', ['session_id'], unique=False)
    op.create_index('ix_adaptive_practice_questions_question_id', 'adaptive_practice_questions', ['question_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_adaptive_practice_questions_question_id', table_name='adaptive_practice_questions')
    op.drop_index('ix_adaptive_practice_questions_session_id', table_name='adaptive_practice_questions')
    op.drop_table('adaptive_practice_questions')

    op.drop_index('ix_adaptive_practice_sessions_status', table_name='adaptive_practice_sessions')
    op.drop_index('ix_adaptive_practice_sessions_user_id', table_name='adaptive_practice_sessions')
    op.drop_table('adaptive_practice_sessions')

    op.drop_index('ix_adaptive_profiles_subject', table_name='adaptive_profiles')
    op.drop_index('ix_adaptive_profiles_user_id', table_name='adaptive_profiles')
    op.drop_table('adaptive_profiles')
