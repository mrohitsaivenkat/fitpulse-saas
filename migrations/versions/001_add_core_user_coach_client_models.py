"""Add core user coach client models

Revision ID: 001_core_models
Revises: 
Create Date: 2026-09-29 22:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001_core_models'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 1. Users Table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), server_default='CLIENT', nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('phone', sa.String(length=30), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)

    # 2. Coaches Table (Tenant / Workspace)
    op.create_table(
        'coaches',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('business_name', sa.String(length=150), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('specialization', sa.String(length=150), nullable=True),
        sa.Column('experience_years', sa.Integer(), server_default='0', nullable=False),
        sa.Column('profile_image', sa.String(length=255), nullable=True),
        sa.Column('location', sa.String(length=150), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('instagram', sa.String(length=100), nullable=True),
        sa.Column('facebook', sa.String(length=100), nullable=True),
        sa.Column('youtube', sa.String(length=100), nullable=True),
        sa.Column('is_public', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_coaches_user_id'), 'coaches', ['user_id'], unique=True)
    op.create_index(op.f('ix_coaches_is_public'), 'coaches', ['is_public'], unique=False)

    # 3. Clients Table (Tenant-Scoped Member)
    op.create_table(
        'clients',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('coach_id', sa.Integer(), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('gender', sa.String(length=20), nullable=True),
        sa.Column('height', sa.Float(), nullable=True),
        sa.Column('current_weight', sa.Float(), nullable=True),
        sa.Column('goal', sa.String(length=200), nullable=True),
        sa.Column('activity_level', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['coach_id'], ['coaches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_clients_user_id'), 'clients', ['user_id'], unique=True)
    op.create_index(op.f('ix_clients_coach_id'), 'clients', ['coach_id'], unique=False)
    op.create_index(op.f('ix_clients_is_active'), 'clients', ['is_active'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_clients_is_active'), table_name='clients')
    op.drop_index(op.f('ix_clients_coach_id'), table_name='clients')
    op.drop_index(op.f('ix_clients_user_id'), table_name='clients')
    op.drop_table('clients')

    op.drop_index(op.f('ix_coaches_is_public'), table_name='coaches')
    op.drop_index(op.f('ix_coaches_user_id'), table_name='coaches')
    op.drop_table('coaches')

    op.drop_index(op.f('ix_users_role'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
