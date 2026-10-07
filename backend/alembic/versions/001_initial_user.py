"""create initial users table

Revision ID: 001_initial_user
Revises: 
Create Date: 2026-10-07 17:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_initial_user'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=255), nullable=False),
        sa.Column('last_name', sa.String(length=255), nullable=True),
        sa.Column('language_code', sa.String(length=10), server_default='en', nullable=False),
        sa.Column('avatar_url', sa.Text(), nullable=True),
        sa.Column('target_score', sa.Integer(), server_default='1400', nullable=False),
        sa.Column('current_score_estimate', sa.Integer(), server_default='700', nullable=False),
        sa.Column('math_estimate', sa.Integer(), server_default='360', nullable=False),
        sa.Column('rw_estimate', sa.Integer(), server_default='340', nullable=False),
        sa.Column('level', sa.Integer(), server_default='1', nullable=False),
        sa.Column('xp', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('last_active_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_telegram_id', 'users', ['telegram_id'], unique=True)
    op.create_index('ix_users_username', 'users', ['username'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_users_username', table_name='users')
    op.drop_index('ix_users_telegram_id', table_name='users')
    op.drop_table('users')
