"""add user full_name

Revision ID: 0004
Revises: 0003
"""
from alembic import op
import sqlalchemy as sa


revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('full_name', sa.String(length=128), nullable=False, server_default=''))


def downgrade():
    op.drop_column('users', 'full_name')
