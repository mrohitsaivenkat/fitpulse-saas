"""Add exercise diet and workout models

Revision ID: 002_exercise_diet_workout
Revises: 001_core_models
Create Date: 2026-09-29 22:20:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_exercise_diet_workout'
down_revision = '001_core_models'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Shared Exercise Library
    op.create_table(
        'exercises',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('muscle_group', sa.String(length=100), nullable=False),
        sa.Column('equipment', sa.String(length=100), nullable=True),
        sa.Column('difficulty', sa.String(length=50), server_default='Intermediate', nullable=False),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column('precautions', sa.Text(), nullable=True),
        sa.Column('video_url', sa.String(length=255), nullable=True),
        sa.Column('image_url', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_exercises_name'), 'exercises', ['name'], unique=False)
    op.create_index(op.f('ix_exercises_category'), 'exercises', ['category'], unique=False)
    op.create_index(op.f('ix_exercises_muscle_group'), 'exercises', ['muscle_group'], unique=False)
    op.create_index(op.f('ix_exercises_is_active'), 'exercises', ['is_active'], unique=False)

    # 2. Diet Plans (Tenant Owned)
    op.create_table(
        'diet_plans',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('coach_id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('daily_calorie_target', sa.Integer(), nullable=True),
        sa.Column('protein_target', sa.Float(), nullable=True),
        sa.Column('carbs_target', sa.Float(), nullable=True),
        sa.Column('fat_target', sa.Float(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['coach_id'], ['coaches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_diet_plans_coach_id'), 'diet_plans', ['coach_id'], unique=False)
    op.create_index(op.f('ix_diet_plans_client_id'), 'diet_plans', ['client_id'], unique=False)
    op.create_index(op.f('ix_diet_plans_is_active'), 'diet_plans', ['is_active'], unique=False)

    # 3. Diet Items
    op.create_table(
        'diet_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('diet_plan_id', sa.Integer(), nullable=False),
        sa.Column('meal_name', sa.String(length=100), nullable=False),
        sa.Column('food_name', sa.String(length=150), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=False),
        sa.Column('calories', sa.Integer(), nullable=True),
        sa.Column('protein', sa.Float(), nullable=True),
        sa.Column('carbohydrates', sa.Float(), nullable=True),
        sa.Column('fat', sa.Float(), nullable=True),
        sa.Column('meal_time', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['diet_plan_id'], ['diet_plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_diet_items_diet_plan_id'), 'diet_items', ['diet_plan_id'], unique=False)

    # 4. Workout Plans (Tenant Owned)
    op.create_table(
        'workout_plans',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('coach_id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['coach_id'], ['coaches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workout_plans_coach_id'), 'workout_plans', ['coach_id'], unique=False)
    op.create_index(op.f('ix_workout_plans_client_id'), 'workout_plans', ['client_id'], unique=False)
    op.create_index(op.f('ix_workout_plans_is_active'), 'workout_plans', ['is_active'], unique=False)

    # 5. Workout Days
    op.create_table(
        'workout_days',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('workout_plan_id', sa.Integer(), nullable=False),
        sa.Column('day_name', sa.String(length=100), nullable=False),
        sa.Column('day_number', sa.Integer(), server_default='1', nullable=False),
        sa.Column('focus', sa.String(length=150), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['workout_plan_id'], ['workout_plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workout_days_workout_plan_id'), 'workout_days', ['workout_plan_id'], unique=False)

    # 6. Workout Exercises
    op.create_table(
        'workout_exercises',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('workout_day_id', sa.Integer(), nullable=False),
        sa.Column('exercise_id', sa.Integer(), nullable=False),
        sa.Column('sets', sa.Integer(), server_default='3', nullable=False),
        sa.Column('reps', sa.String(length=50), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('rest_seconds', sa.Integer(), server_default='90', nullable=True),
        sa.Column('order_index', sa.Integer(), server_default='1', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['workout_day_id'], ['workout_days.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['exercise_id'], ['exercises.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workout_exercises_workout_day_id'), 'workout_exercises', ['workout_day_id'], unique=False)
    op.create_index(op.f('ix_workout_exercises_exercise_id'), 'workout_exercises', ['exercise_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_workout_exercises_exercise_id'), table_name='workout_exercises')
    op.drop_index(op.f('ix_workout_exercises_workout_day_id'), table_name='workout_exercises')
    op.drop_table('workout_exercises')

    op.drop_index(op.f('ix_workout_days_workout_plan_id'), table_name='workout_days')
    op.drop_table('workout_days')

    op.drop_index(op.f('ix_workout_plans_is_active'), table_name='workout_plans')
    op.drop_index(op.f('ix_workout_plans_client_id'), table_name='workout_plans')
    op.drop_index(op.f('ix_workout_plans_coach_id'), table_name='workout_plans')
    op.drop_table('workout_plans')

    op.drop_index(op.f('ix_diet_items_diet_plan_id'), table_name='diet_items')
    op.drop_table('diet_items')

    op.drop_index(op.f('ix_diet_plans_is_active'), table_name='diet_plans')
    op.drop_index(op.f('ix_diet_plans_client_id'), table_name='diet_plans')
    op.drop_index(op.f('ix_diet_plans_coach_id'), table_name='diet_plans')
    op.drop_table('diet_plans')

    op.drop_index(op.f('ix_exercises_is_active'), table_name='exercises')
    op.drop_index(op.f('ix_exercises_muscle_group'), table_name='exercises')
    op.drop_index(op.f('ix_exercises_category'), table_name='exercises')
    op.drop_index(op.f('ix_exercises_name'), table_name='exercises')
    op.drop_table('exercises')
