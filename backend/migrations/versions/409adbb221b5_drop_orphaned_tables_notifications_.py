"""drop_orphaned_tables_notifications_login_attempts_survey_activations

Revision ID: 409adbb221b5
Revises: ee5ffabb9b99
Create Date: 2026-07-12 19:50:40.411054

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '409adbb221b5'
down_revision: Union[str, Sequence[str], None] = 'ee5ffabb9b99'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop three orphaned tables whose Python models have been removed."""
    op.drop_table('survey_activations')
    op.drop_table('login_attempts')
    op.drop_table('notifications')


def downgrade() -> None:
    """Recreate the orphaned tables in case of rollback."""
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('channel', sa.Enum('EMAIL', name='notification_channel_enum'), default='EMAIL'),
        sa.Column('type', sa.Enum('OTP', 'ACTIVATION', 'INVITATION', 'REMINDER', 'RESET_PASSWORD', name='notification_type_enum'), nullable=False),
        sa.Column('recipient', sa.String(255), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'SENT', 'FAILED', name='notification_status_enum'), default='PENDING'),
        sa.Column('provider_response', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), default=0),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'login_attempts',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('success', sa.Boolean(), default=False),
        sa.Column('attempted_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'survey_activations',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('survey_id', sa.Integer(), sa.ForeignKey('surveys.id'), nullable=False),
        sa.Column('activated_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('activated_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
