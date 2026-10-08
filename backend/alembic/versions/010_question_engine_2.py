"""question engine 2 extensions

Revision ID: 010_question_engine_2
Revises: 009_ai_tutor
Create Date: 2026-10-08 08:38:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '010_question_engine_2'
down_revision: Union[str, None] = '009_ai_tutor'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add template and variant tracking columns to questions table
    with op.batch_alter_table('questions') as batch_op:
        batch_op.add_column(sa.Column('template_id', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('variant_group', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('source_type', sa.String(length=32), server_default='ORIGINAL', nullable=False))
        batch_op.add_column(sa.Column('metadata_json', sa.Text(), nullable=True))
        batch_op.create_index('ix_questions_template_id', ['template_id'])
        batch_op.create_index('ix_questions_variant_group', ['variant_group'])
        batch_op.create_index('ix_questions_source_type', ['source_type'])


def downgrade() -> None:
    with op.batch_alter_table('questions') as batch_op:
        batch_op.drop_index('ix_questions_source_type')
        batch_op.drop_index('ix_questions_variant_group')
        batch_op.drop_index('ix_questions_template_id')
        batch_op.drop_column('metadata_json')
        batch_op.drop_column('source_type')
        batch_op.drop_column('variant_group')
        batch_op.drop_column('template_id')
