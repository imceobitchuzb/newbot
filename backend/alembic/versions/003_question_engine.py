"""create question engine tables

Revision ID: 003_question_engine
Revises: 002_user_profile
Create Date: 2026-10-07 18:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003_question_engine'
down_revision: Union[str, None] = '002_user_profile'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Passages table
    op.create_table(
        'passages',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('passage_text', sa.Text(), nullable=False),
        sa.Column('source_info', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # 2. Questions table
    op.create_table(
        'questions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('passage_id', sa.Uuid(), nullable=True),
        sa.Column('subject', sa.String(length=32), nullable=False),
        sa.Column('domain', sa.String(length=64), nullable=False),
        sa.Column('skill', sa.String(length=128), nullable=False),
        sa.Column('subskill', sa.String(length=128), nullable=True),
        sa.Column('question_type', sa.String(length=32), server_default='MULTIPLE_CHOICE', nullable=False),
        sa.Column('difficulty', sa.String(length=16), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('hint', sa.Text(), nullable=True),
        sa.Column('sat_shortcut', sa.Text(), nullable=True),
        sa.Column('estimated_time_seconds', sa.Integer(), server_default='75', nullable=False),
        sa.Column('desmos_allowed', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('desmos_recommended', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='PUBLISHED', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['passage_id'], ['passages.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_questions_passage_id', 'questions', ['passage_id'], unique=False)
    op.create_index('ix_questions_subject', 'questions', ['subject'], unique=False)
    op.create_index('ix_questions_domain', 'questions', ['domain'], unique=False)
    op.create_index('ix_questions_skill', 'questions', ['skill'], unique=False)
    op.create_index('ix_questions_difficulty', 'questions', ['difficulty'], unique=False)
    op.create_index('ix_questions_status', 'questions', ['status'], unique=False)

    # 3. Question Options table
    op.create_table(
        'question_options',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('question_id', sa.Uuid(), nullable=False),
        sa.Column('label', sa.String(length=4), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('order_index', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_correct', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_question_options_question_id', 'question_options', ['question_id'], unique=False)

    # 4. Question Attempts table
    op.create_table(
        'question_attempts',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('question_id', sa.Uuid(), nullable=False),
        sa.Column('selected_option_id', sa.Uuid(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        sa.Column('time_spent_seconds', sa.Integer(), server_default='0', nullable=False),
        sa.Column('answered_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['selected_option_id'], ['question_options.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_question_attempts_user_id', 'question_attempts', ['user_id'], unique=False)
    op.create_index('ix_question_attempts_question_id', 'question_attempts', ['question_id'], unique=False)
    op.create_index('ix_question_attempts_answered_at', 'question_attempts', ['answered_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_question_attempts_answered_at', table_name='question_attempts')
    op.drop_index('ix_question_attempts_question_id', table_name='question_attempts')
    op.drop_index('ix_question_attempts_user_id', table_name='question_attempts')
    op.drop_table('question_attempts')

    op.drop_index('ix_question_options_question_id', table_name='question_options')
    op.drop_table('question_options')

    op.drop_index('ix_questions_status', table_name='questions')
    op.drop_index('ix_questions_difficulty', table_name='questions')
    op.drop_index('ix_questions_skill', table_name='questions')
    op.drop_index('ix_questions_domain', table_name='questions')
    op.drop_index('ix_questions_subject', table_name='questions')
    op.drop_index('ix_questions_passage_id', table_name='questions')
    op.drop_table('questions')

    op.drop_table('passages')
