"""create desmos lab tables

Revision ID: 008_desmos_lab
Revises: 007_adaptive_learning
Create Date: 2026-10-07 20:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '008_desmos_lab'
down_revision: Union[str, None] = '007_adaptive_learning'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. desmos_techniques
    op.create_table(
        'desmos_techniques',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('slug', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('technique_type', sa.String(length=64), nullable=False),
        sa.Column('subject', sa.String(length=32), server_default='MATH', nullable=False),
        sa.Column('difficulty', sa.String(length=16), server_default='MEDIUM', nullable=False),
        sa.Column('when_to_use', sa.Text(), nullable=False),
        sa.Column('when_not_to_use', sa.Text(), nullable=False),
        sa.Column('steps', sa.JSON(), nullable=False),
        sa.Column('common_mistakes', sa.JSON(), nullable=False),
        sa.Column('sat_tip', sa.Text(), nullable=False),
        sa.Column('example_question_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['example_question_id'], ['questions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug', name='uq_desmos_technique_slug'),
    )
    op.create_index('ix_desmos_techniques_slug', 'desmos_techniques', ['slug'], unique=True)
    op.create_index('ix_desmos_techniques_technique_type', 'desmos_techniques', ['technique_type'], unique=False)

    # 2. question_desmos_techniques
    op.create_table(
        'question_desmos_techniques',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('question_id', sa.Uuid(), nullable=False),
        sa.Column('technique_id', sa.Uuid(), nullable=False),
        sa.Column('technique_type', sa.String(length=64), nullable=False),
        sa.Column('is_primary', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['technique_id'], ['desmos_techniques.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('question_id', 'technique_id', name='uq_question_desmos_technique'),
    )
    op.create_index('ix_question_desmos_techniques_question_id', 'question_desmos_techniques', ['question_id'], unique=False)
    op.create_index('ix_question_desmos_techniques_technique_id', 'question_desmos_techniques', ['technique_id'], unique=False)
    op.create_index('ix_question_desmos_techniques_technique_type', 'question_desmos_techniques', ['technique_type'], unique=False)

    # 3. desmos_practice_sessions
    op.create_table(
        'desmos_practice_sessions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('technique_id', sa.Uuid(), nullable=True),
        sa.Column('technique_type', sa.String(length=64), nullable=True),
        sa.Column('difficulty', sa.String(length=16), nullable=True),
        sa.Column('target_count', sa.Integer(), server_default='10', nullable=False),
        sa.Column('completed_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('correct_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='IN_PROGRESS', nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['technique_id'], ['desmos_techniques.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_desmos_practice_sessions_user_id', 'desmos_practice_sessions', ['user_id'], unique=False)
    op.create_index('ix_desmos_practice_sessions_status', 'desmos_practice_sessions', ['status'], unique=False)
    op.create_index('ix_desmos_practice_sessions_technique_id', 'desmos_practice_sessions', ['technique_id'], unique=False)

    # 4. desmos_practice_questions
    op.create_table(
        'desmos_practice_questions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('session_id', sa.Uuid(), nullable=False),
        sa.Column('question_id', sa.Uuid(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('technique_type', sa.String(length=64), nullable=True),
        sa.Column('selected_option_id', sa.Uuid(), nullable=True),
        sa.Column('attempt_id', sa.Uuid(), nullable=True),
        sa.Column('is_answered', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=True),
        sa.Column('desmos_used', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('answered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['desmos_practice_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['selected_option_id'], ['question_options.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['attempt_id'], ['question_attempts.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'order_index', name='uq_desmos_session_order'),
        sa.UniqueConstraint('session_id', 'question_id', name='uq_desmos_session_question'),
    )
    op.create_index('ix_desmos_practice_questions_session_id', 'desmos_practice_questions', ['session_id'], unique=False)
    op.create_index('ix_desmos_practice_questions_question_id', 'desmos_practice_questions', ['question_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_desmos_practice_questions_question_id', table_name='desmos_practice_questions')
    op.drop_index('ix_desmos_practice_questions_session_id', table_name='desmos_practice_questions')
    op.drop_table('desmos_practice_questions')

    op.drop_index('ix_desmos_practice_sessions_technique_id', table_name='desmos_practice_sessions')
    op.drop_index('ix_desmos_practice_sessions_status', table_name='desmos_practice_sessions')
    op.drop_index('ix_desmos_practice_sessions_user_id', table_name='desmos_practice_sessions')
    op.drop_table('desmos_practice_sessions')

    op.drop_index('ix_question_desmos_techniques_technique_type', table_name='question_desmos_techniques')
    op.drop_index('ix_question_desmos_techniques_technique_id', table_name='question_desmos_techniques')
    op.drop_index('ix_question_desmos_techniques_question_id', table_name='question_desmos_techniques')
    op.drop_table('question_desmos_techniques')

    op.drop_index('ix_desmos_techniques_technique_type', table_name='desmos_techniques')
    op.drop_index('ix_desmos_techniques_slug', table_name='desmos_techniques')
    op.drop_table('desmos_techniques')
