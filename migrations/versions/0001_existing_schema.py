"""Record the schema shipped before managed migrations.

Revision ID: 0001_existing_schema
Revises:
"""
from alembic import op
import sqlalchemy as sa


revision = '0001_existing_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=80), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id'), sa.UniqueConstraint('username'))
    op.create_table('customer',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=180), nullable=False),
        sa.Column('phone', sa.String(length=60), nullable=True),
        sa.Column('email', sa.String(length=180), nullable=True),
        sa.Column('address', sa.String(length=300), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'))
    op.create_table('audit',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=80), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'))
    op.create_table('job',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('service', sa.String(length=120), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=True),
        sa.Column('preferred_date', sa.String(length=40), nullable=True),
        sa.Column('appointment_date', sa.String(length=40), nullable=True),
        sa.Column('arrival_window', sa.String(length=80), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('checklist', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customer.id']),
        sa.PrimaryKeyConstraint('id'))
    op.create_table('estimate',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('labor_hours', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('hourly_rate', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('materials', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('other', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('markup', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('total', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['job.id']),
        sa.PrimaryKeyConstraint('id'))
    op.create_table('photo',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=200), nullable=False),
        sa.Column('original_name', sa.String(length=200), nullable=False),
        sa.Column('category', sa.String(length=30), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['job.id']),
        sa.PrimaryKeyConstraint('id'))


def downgrade():
    op.drop_table('photo')
    op.drop_table('estimate')
    op.drop_table('job')
    op.drop_table('audit')
    op.drop_table('customer')
    op.drop_table('user')

