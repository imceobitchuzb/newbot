"""create diagnostic module tables

Revision ID: 004_diagnostic_module
Revises: 003_question_engine
Create Date: 2026-10-07 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '004_diagnostic_module'
down_revision: Union[str, None] = '003_question_engine'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Diagnostic Sessions table
    op.create_table(
        'diagnostic_sessions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='IN_PROGRESS', nullable=False),
        sa.Column('current_module', sa.String(length=32), server_default='MATH', nullable=False),
        sa.Column('current_question_index', sa.Integer(), server_default='0', nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_diagnostic_sessions_user_id', 'diagnostic_sessions', ['user_id'], unique=False)
    op.create_index('ix_diagnostic_sessions_status', 'diagnostic_sessions', ['status'], unique=False)

    # 2. Diagnostic Modules table
    op.create_table(
        'diagnostic_modules',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('session_id', sa.Uuid(), nullable=False),
        sa.Column('subject', sa.String(length=32), nullable=False),
        sa.Column('module_number', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='NOT_STARTED', nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['diagnostic_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'module_number', name='uq_diagnostic_modules_session_module_number'),
    )
    op.create_index('ix_diagnostic_modules_session_id', 'diagnostic_modules', ['session_id'], unique=False)

    # 3. Diagnostic Questions table
    op.create_table(
        'diagnostic_questions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('module_id', sa.Uuid(), nullable=False),
        sa.Column('question_id', sa.Uuid(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('selected_option_id', sa.Uuid(), nullable=True),
        sa.Column('attempt_id', sa.Uuid(), nullable=True),
        sa.Column('is_answered', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('time_spent_seconds', sa.Integer(), server_default='0', nullable=False),
        sa.Column('answered_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['attempt_id'], ['question_attempts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['module_id'], ['diagnostic_modules.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['selected_option_id'], ['question_options.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('module_id', 'order_index', name='uq_diagnostic_questions_module_order'),
        sa.UniqueConstraint('module_id', 'question_id', name='uq_diagnostic_questions_module_question'),
    )
    op.create_index('ix_diagnostic_questions_module_id', 'diagnostic_questions', ['module_id'], unique=False)
    op.create_index('ix_diagnostic_questions_question_id', 'diagnostic_questions', ['question_id'], unique=False)

    # 4. Diagnostic Results table
    op.create_table(
        'diagnostic_results',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('session_id', sa.Uuid(), nullable=False),
        sa.Column('math_correct', sa.Integer(), nullable=False),
        sa.Column('math_total', sa.Integer(), server_default='20', nullable=False),
        sa.Column('rw_correct', sa.Integer(), nullable=False),
        sa.Column('rw_total', sa.Integer(), server_default='20', nullable=False),
        sa.Column('math_accuracy', sa.Float(), nullable=False),
        sa.Column('rw_accuracy', sa.Float(), nullable=False),
        sa.Column('total_accuracy', sa.Float(), nullable=False),
        sa.Column('estimated_math_low', sa.Integer(), nullable=False),
        sa.Column('estimated_math_high', sa.Integer(), nullable=False),
        sa.Column('estimated_rw_low', sa.Integer(), nullable=False),
        sa.Column('estimated_rw_high', sa.Integer(), nullable=False),
        sa.Column('estimated_total_low', sa.Integer(), nullable=False),
        sa.Column('estimated_total_high', sa.Integer(), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), server_default='0', nullable=False),
        sa.Column('domain_breakdown', sa.JSON(), nullable=False),
        sa.Column('weak_domains', sa.JSON(), nullable=False),
        sa.Column('strong_domains', sa.JSON(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['diagnostic_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id'),
    )
    op.create_index('ix_diagnostic_results_session_id', 'diagnostic_results', ['session_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_diagnostic_results_session_id', table_name='diagnostic_results')
    op.drop_table('diagnostic_results')

    op.drop_index('ix_diagnostic_questions_question_id', table_name='diagnostic_questions')
    op.drop_index('ix_diagnostic_questions_module_id', table_name='diagnostic_questions')
    op.drop_table('diagnostic_questions')

    op.drop_index('ix_diagnostic_modules_session_id', table_name='diagnostic_modules')
    op.drop_table('diagnostic_modules')

    op.drop_index('ix_diagnostic_sessions_status', table_name='diagnostic_sessions')
    op.drop_index('ix_diagnostic_sessions_user_id', table_name='diagnostic_sessions')
    op.drop_table('diagnostic_sessions')
