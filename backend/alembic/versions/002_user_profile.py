"""create user_profiles table

Revision ID: 002_user_profile
Revises: 001_initial_user
Create Date: 2026-10-07 18:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_user_profile'
down_revision: Union[str, None] = '001_initial_user'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('target_score', sa.Integer(), server_default='1400', nullable=False),
        sa.Column('diagnostic_status', sa.String(length=32), server_default='not_started', nullable=False),
        sa.Column('study_goal', sa.String(length=255), server_default='Score 1400+ in 4 months', nullable=False),
        sa.Column('daily_goal_minutes', sa.Integer(), server_default='30', nullable=False),
        sa.Column('math_estimate', sa.Integer(), nullable=True),
        sa.Column('rw_estimate', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_user_profiles_user_id', 'user_profiles', ['user_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_user_profiles_user_id', table_name='user_profiles')
    op.drop_table('user_profiles')
