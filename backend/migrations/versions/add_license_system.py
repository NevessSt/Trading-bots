"""Add license system fields to User table

Revision ID: add_license_system
Revises: 
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'add_license_system'
down_revision = '7b14cfde174f'
branch_labels = None
depends_on = None


def upgrade():
    """Add license system fields to users table"""
    # Add license-related columns to users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        # Check if columns don't already exist before adding
        batch_op.add_column(sa.Column('license_key', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('license_type', sa.String(length=20), nullable=False, server_default='free'))
        batch_op.add_column(sa.Column('license_expires', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('license_activated', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('license_status', sa.String(length=20), nullable=False, server_default='active'))
        batch_op.add_column(sa.Column('max_bots', sa.Integer(), nullable=False, server_default='1'))
        batch_op.add_column(sa.Column('max_api_keys', sa.Integer(), nullable=False, server_default='1'))
        batch_op.add_column(sa.Column('permissions', sa.JSON(), nullable=True))
    
    # Create api_keys table if it doesn't exist
    op.create_table('api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('exchange', sa.String(length=50), nullable=False),
        sa.Column('key_name', sa.String(length=100), nullable=False),
        sa.Column('api_key', sa.String(length=255), nullable=False),
        sa.Column('api_secret_encrypted', sa.Text(), nullable=False),
        sa.Column('passphrase_encrypted', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('is_testnet', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('permissions', sa.JSON(), nullable=True),
        sa.Column('last_used', sa.DateTime(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_api_keys_user_id'), 'api_keys', ['user_id'], unique=False)
    op.create_index(op.f('ix_api_keys_exchange'), 'api_keys', ['exchange'], unique=False)
    op.create_index(op.f('ix_users_license_type'), 'users', ['license_type'], unique=False)
    op.create_index(op.f('ix_users_license_status'), 'users', ['license_status'], unique=False)


def downgrade():
    """Remove license system fields from users table"""
    # Drop indexes
    op.drop_index(op.f('ix_users_license_status'), table_name='users')
    op.drop_index(op.f('ix_users_license_type'), table_name='users')
    op.drop_index(op.f('ix_api_keys_exchange'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_user_id'), table_name='api_keys')
    
    # Drop api_keys table
    op.drop_table('api_keys')
    
    # Remove license-related columns from users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('permissions')
        batch_op.drop_column('max_api_keys')
        batch_op.drop_column('max_bots')
        batch_op.drop_column('license_status')
        batch_op.drop_column('license_activated')
        batch_op.drop_column('license_expires')
        batch_op.drop_column('license_type')
        batch_op.drop_column('license_key')