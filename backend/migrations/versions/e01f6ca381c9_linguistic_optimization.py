"""linguistic_optimization

Revision ID: e01f6ca381c9
Revises: 6946d6a3c80d
Create Date: 2026-07-08 02:00:32.861126

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e01f6ca381c9'
down_revision: Union[str, Sequence[str], None] = '6946d6a3c80d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # sectors
    op.alter_column('sectors', 'name_fr', new_column_name='name', existing_type=sa.String(255))
    op.drop_column('sectors', 'name_en')
    op.drop_column('sectors', 'name_ar')
    
    # activities
    op.alter_column('activities', 'name_fr', new_column_name='name', existing_type=sa.String(255))
    op.drop_column('activities', 'name_en')
    op.drop_column('activities', 'name_ar')

def downgrade() -> None:
    """Downgrade schema."""
    # sectors
    op.alter_column('sectors', 'name', new_column_name='name_fr')
    op.add_column('sectors', sa.Column('name_en', sa.String(255), nullable=True))
    op.add_column('sectors', sa.Column('name_ar', sa.String(255), nullable=True))

    # activities
    op.alter_column('activities', 'name', new_column_name='name_fr')
    op.add_column('activities', sa.Column('name_en', sa.String(255), nullable=True))
    op.add_column('activities', sa.Column('name_ar', sa.String(255), nullable=True))
