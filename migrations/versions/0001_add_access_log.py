"""Add AccessLog table

Revision ID: 0001_add_access_log
Revises: 
Create Date: 2026-02-06 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_add_access_log'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'access_log',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=512), nullable=True),
        sa.Column('path', sa.String(length=255), nullable=True),
        sa.Column('method', sa.String(length=10), nullable=True),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )
    op.create_index('ix_access_log_timestamp', 'access_log', ['timestamp'])
    op.create_index('ix_access_log_user_id', 'access_log', ['user_id'])


def downgrade():
    op.drop_index('ix_access_log_user_id', table_name='access_log')
    op.drop_index('ix_access_log_timestamp', table_name='access_log')
    op.drop_table('access_log')
