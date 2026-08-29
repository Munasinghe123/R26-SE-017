"""initial schema for SDLC multi-agent system

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-22 16:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Tenants table
    op.create_table(
        'tenants',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    # Default dev tenant insert
    op.execute("INSERT INTO tenants (id, name) VALUES ('dev', 'Development') ON CONFLICT DO NOTHING;")

    # 2. Jobs table
    op.create_table(
        'jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', sa.Text(), nullable=False),
        sa.Column('created_by', sa.Text(), server_default='dev-user', nullable=False),
        sa.Column('project_name', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False),
        sa.Column('current_stage', sa.Text(), nullable=True),
        sa.Column('input_kind', sa.Text(), nullable=False),
        sa.Column('input_uri', sa.Text(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_jobs_tenant_status', 'jobs', ['tenant_id', 'status'], unique=False)
    op.create_index('idx_jobs_created_at', 'jobs', [sa.text('created_at DESC')], unique=False)

    # 3. Stage runs table
    op.create_table(
        'stage_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('stage', sa.Text(), nullable=False),
        sa.Column('attempt', sa.Integer(), server_default='1', nullable=False),
        sa.Column('status', sa.Text(), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('schema_version', sa.Text(), server_default='1.0', nullable=False),
        sa.Column('llm_backend', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('finished_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_stage_runs_job_stage', 'stage_runs', ['job_id', 'stage'], unique=False)
    op.create_index('idx_stage_runs_payload', 'stage_runs', ['payload'], postgresql_using='gin')

    # 4. Artifacts table
    op.create_table(
        'artifacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('stage', sa.Text(), nullable=False),
        sa.Column('kind', sa.Text(), nullable=False),
        sa.Column('filename', sa.Text(), nullable=False),
        sa.Column('uri', sa.Text(), nullable=False),
        sa.Column('mime_type', sa.Text(), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_artifacts_job_stage', 'artifacts', ['job_id', 'stage'], unique=False)

    # 5. Architecture candidates table (THE THESIS DATASET)
    op.create_table(
        'architecture_candidates',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('case_study_id', sa.Text(), nullable=False),
        sa.Column('llm_model', sa.Text(), nullable=False),
        sa.Column('seed', sa.Integer(), nullable=False),
        sa.Column('detected_style', sa.Text(), nullable=False),
        sa.Column('style_confidence', sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column('rts', sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column('qac', sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column('ci', sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column('cos', sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column('ssm1', sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column('ssm2', sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column('cas', sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column('verdict', sa.Text(), nullable=False),
        sa.Column('rank_position', sa.Integer(), nullable=True),
        sa.Column('cam', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_arch_cand_case_model', 'architecture_candidates', ['case_study_id', 'llm_model'], unique=False)
    op.create_index('idx_arch_cand_cas', 'architecture_candidates', [sa.text('cas DESC')], unique=False)


def downgrade() -> None:
    op.drop_index('idx_arch_cand_cas', table_name='architecture_candidates')
    op.drop_index('idx_arch_cand_case_model', table_name='architecture_candidates')
    op.drop_table('architecture_candidates')

    op.drop_index('idx_artifacts_job_stage', table_name='artifacts')
    op.drop_table('artifacts')

    op.drop_index('idx_stage_runs_payload', table_name='stage_runs')
    op.drop_index('idx_stage_runs_job_stage', table_name='stage_runs')
    op.drop_table('stage_runs')

    op.drop_index('idx_jobs_created_at', table_name='jobs')
    op.drop_index('idx_jobs_tenant_status', table_name='jobs')
    op.drop_table('jobs')

    op.drop_table('tenants')
