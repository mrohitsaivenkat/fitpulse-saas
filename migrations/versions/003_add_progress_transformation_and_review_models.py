"""Add progress transformation and review models

Revision ID: 003_progress_trans_reviews
Revises: 002_exercise_diet_workout
Create Date: 2026-09-29 22:25:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_progress_trans_reviews'
down_revision = '002_exercise_diet_workout'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Progress (Biometrics Tracking)
    op.create_table(
        'progress',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('body_fat_percentage', sa.Float(), nullable=True),
        sa.Column('muscle_mass', sa.Float(), nullable=True),
        sa.Column('waist', sa.Float(), nullable=True),
        sa.Column('chest', sa.Float(), nullable=True),
        sa.Column('arms', sa.Float(), nullable=True),
        sa.Column('thighs', sa.Float(), nullable=True),
        sa.Column('hips', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_progress_client_id'), 'progress', ['client_id'], unique=False)
    op.create_index(op.f('ix_progress_date'), 'progress', ['date'], unique=False)

    # 2. Measurements (Detailed Circumference Tracking)
    op.create_table(
        'measurements',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('measurement_date', sa.Date(), nullable=False),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('body_fat_percentage', sa.Float(), nullable=True),
        sa.Column('neck', sa.Float(), nullable=True),
        sa.Column('shoulders', sa.Float(), nullable=True),
        sa.Column('chest', sa.Float(), nullable=True),
        sa.Column('waist', sa.Float(), nullable=True),
        sa.Column('abdomen', sa.Float(), nullable=True),
        sa.Column('hips', sa.Float(), nullable=True),
        sa.Column('left_arm', sa.Float(), nullable=True),
        sa.Column('right_arm', sa.Float(), nullable=True),
        sa.Column('left_thigh', sa.Float(), nullable=True),
        sa.Column('right_thigh', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measurements_client_id'), 'measurements', ['client_id'], unique=False)
    op.create_index(op.f('ix_measurements_measurement_date'), 'measurements', ['measurement_date'], unique=False)

    # 3. Progress Photos (Visual Tracking)
    op.create_table(
        'progress_photos',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('photo_type', sa.String(length=20), nullable=False),
        sa.Column('file_path', sa.String(length=255), nullable=False),
        sa.Column('captured_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_private', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_progress_photos_client_id'), 'progress_photos', ['client_id'], unique=False)
    op.create_index(op.f('ix_progress_photos_captured_at'), 'progress_photos', ['captured_at'], unique=False)
    op.create_index(op.f('ix_progress_photos_is_private'), 'progress_photos', ['is_private'], unique=False)

    # 4. Transformations (Showcase Case Studies)
    op.create_table(
        'transformations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('coach_id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('before_photo', sa.String(length=255), nullable=True),
        sa.Column('after_photo', sa.String(length=255), nullable=True),
        sa.Column('duration_text', sa.String(length=100), nullable=True),
        sa.Column('achievement_text', sa.Text(), nullable=True),
        sa.Column('is_public', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['coach_id'], ['coaches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transformations_coach_id'), 'transformations', ['coach_id'], unique=False)
    op.create_index(op.f('ix_transformations_client_id'), 'transformations', ['client_id'], unique=False)
    op.create_index(op.f('ix_transformations_is_public'), 'transformations', ['is_public'], unique=False)

    # 5. Transformation Consents (Explicit Privacy Grant)
    op.create_table(
        'transformation_consents',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('transformation_id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('consent_given', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('consent_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('consent_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['transformation_id'], ['transformations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transformation_consents_transformation_id'), 'transformation_consents', ['transformation_id'], unique=False)
    op.create_index(op.f('ix_transformation_consents_client_id'), 'transformation_consents', ['client_id'], unique=False)
    op.create_index(op.f('ix_transformation_consents_consent_given'), 'transformation_consents', ['consent_given'], unique=False)

    # 6. Reviews (Feedback & Ratings)
    op.create_table(
        'reviews',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('coach_id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_public', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('is_approved', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='ck_reviews_rating_range'),
        sa.ForeignKeyConstraint(['coach_id'], ['coaches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reviews_coach_id'), 'reviews', ['coach_id'], unique=False)
    op.create_index(op.f('ix_reviews_client_id'), 'reviews', ['client_id'], unique=False)
    op.create_index(op.f('ix_reviews_is_public'), 'reviews', ['is_public'], unique=False)
    op.create_index(op.f('ix_reviews_is_approved'), 'reviews', ['is_approved'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_reviews_is_approved'), table_name='reviews')
    op.drop_index(op.f('ix_reviews_is_public'), table_name='reviews')
    op.drop_index(op.f('ix_reviews_client_id'), table_name='reviews')
    op.drop_index(op.f('ix_reviews_coach_id'), table_name='reviews')
    op.drop_table('reviews')

    op.drop_index(op.f('ix_transformation_consents_consent_given'), table_name='transformation_consents')
    op.drop_index(op.f('ix_transformation_consents_client_id'), table_name='transformation_consents')
    op.drop_index(op.f('ix_transformation_consents_transformation_id'), table_name='transformation_consents')
    op.drop_table('transformation_consents')

    op.drop_index(op.f('ix_transformations_is_public'), table_name='transformations')
    op.drop_index(op.f('ix_transformations_client_id'), table_name='transformations')
    op.drop_index(op.f('ix_transformations_coach_id'), table_name='transformations')
    op.drop_table('transformations')

    op.drop_index(op.f('ix_progress_photos_is_private'), table_name='progress_photos')
    op.drop_index(op.f('ix_progress_photos_captured_at'), table_name='progress_photos')
    op.drop_index(op.f('ix_progress_photos_client_id'), table_name='progress_photos')
    op.drop_table('progress_photos')

    op.drop_index(op.f('ix_measurements_measurement_date'), table_name='measurements')
    op.drop_index(op.f('ix_measurements_client_id'), table_name='measurements')
    op.drop_table('measurements')

    op.drop_index(op.f('ix_progress_date'), table_name='progress')
    op.drop_index(op.f('ix_progress_client_id'), table_name='progress')
    op.drop_table('progress')
