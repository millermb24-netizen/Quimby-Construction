"""Add reusable, printable job reports.

Revision ID: 0002_job_reports
Revises: 0001_existing_schema
"""
from alembic import op
import sqlalchemy as sa


revision = '0002_job_reports'
down_revision = '0001_existing_schema'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('report_template',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('services_intro', sa.Text(), nullable=True),
        sa.Column('findings_intro', sa.Text(), nullable=True),
        sa.Column('recommendations_intro', sa.Text(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'), sa.UniqueConstraint('name'))
    op.create_table('job_report',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=180), nullable=False),
        sa.Column('report_date', sa.String(length=10), nullable=False),
        sa.Column('services_performed', sa.Text(), nullable=False),
        sa.Column('findings', sa.Text(), nullable=False),
        sa.Column('recommendations', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('finalized_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['job.id']),
        sa.ForeignKeyConstraint(['template_id'], ['report_template.id']),
        sa.PrimaryKeyConstraint('id'))
    op.create_index(op.f('ix_job_report_job_id'), 'job_report', ['job_id'], unique=False)
    op.create_table('report_photo',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('photo_id', sa.Integer(), nullable=False),
        sa.Column('caption', sa.String(length=300), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['photo_id'], ['photo.id']),
        sa.ForeignKeyConstraint(['report_id'], ['job_report.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('report_id', 'photo_id', name='uq_report_photo'))
    op.create_index(op.f('ix_report_photo_report_id'), 'report_photo', ['report_id'], unique=False)
    op.create_table('report_delivery',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('recipient', sa.String(length=180), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('note', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['report_id'], ['job_report.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'))
    op.create_index(op.f('ix_report_delivery_report_id'), 'report_delivery', ['report_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_report_delivery_report_id'), table_name='report_delivery')
    op.drop_table('report_delivery')
    op.drop_index(op.f('ix_report_photo_report_id'), table_name='report_photo')
    op.drop_table('report_photo')
    op.drop_index(op.f('ix_job_report_job_id'), table_name='job_report')
    op.drop_table('job_report')
    op.drop_table('report_template')

