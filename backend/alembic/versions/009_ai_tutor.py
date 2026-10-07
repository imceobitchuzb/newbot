"""create ai tutor tables

Revision ID: 009_ai_tutor
Revises: 008_desmos_lab
Create Date: 2026-10-07 21:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '009_ai_tutor'
down_revision: Union[str, None] = '008_desmos_lab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. tutor_conversations
    op.create_table(
        'tutor_conversations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('context_type', sa.String(length=64), server_default='GENERAL', nullable=False),
        sa.Column('context_id', sa.String(length=128), nullable=True),
        sa.Column('subject', sa.String(length=32), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_tutor_conversations_user_id', 'tutor_conversations', ['user_id'], unique=False)
    op.create_index('ix_tutor_conversations_context_type', 'tutor_conversations', ['context_type'], unique=False)

    # 2. tutor_messages
    op.create_table(
        'tutor_messages',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('conversation_id', sa.Uuid(), nullable=False),
        sa.Column('role', sa.String(length=32), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('mode', sa.String(length=32), nullable=True),
        sa.Column('token_count', sa.Integer(), nullable=True),
        sa.Column('model', sa.String(length=64), nullable=True),
        sa.Column('actions', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['tutor_conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_tutor_messages_conversation_id', 'tutor_messages', ['conversation_id'], unique=False)
    op.create_index('ix_tutor_messages_created_at', 'tutor_messages', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_tutor_messages_created_at', table_name='tutor_messages')
    op.drop_index('ix_tutor_messages_conversation_id', table_name='tutor_messages')
    op.drop_table('tutor_messages')

    op.drop_index('ix_tutor_conversations_context_type', table_name='tutor_conversations')
    op.drop_index('ix_tutor_conversations_user_id', table_name='tutor_conversations')
    op.drop_table('tutor_conversations')
