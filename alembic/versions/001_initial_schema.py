"""Initial schema creation for Phase E1.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-01-05 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create initial schema."""
    
    # Create events table
    op.create_table(
        'events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_events_display_name', 'events', ['display_name'])
    op.create_index('ix_events_created_at', 'events', ['created_at'])
    
    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_sessions_event_id', 'sessions', ['event_id'])
    op.create_index('ix_sessions_created_at', 'sessions', ['created_at'])
    
    # Create projects table
    op.create_table(
        'projects',
        sa.Column('id', sa.String(255), nullable=False),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('artifacts_count', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_projects_event_id', 'projects', ['event_id'])
    op.create_index('ix_projects_status', 'projects', ['status'])
    op.create_index('ix_projects_created_at', 'projects', ['created_at'])
    op.create_index('ix_projects_event_id_status', 'projects', ['event_id', 'status'])
    
    # Create knowledge_artifacts table
    op.create_table(
        'knowledge_artifacts',
        sa.Column('id', sa.String(255), nullable=False),
        sa.Column('project_id', sa.String(255), nullable=False),
        sa.Column('artifact_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('source', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('extraction_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ka_project_id', 'knowledge_artifacts', ['project_id'])
    op.create_index('ix_ka_status', 'knowledge_artifacts', ['status'])
    op.create_index('ix_ka_type', 'knowledge_artifacts', ['artifact_type'])
    op.create_index('ix_ka_created_at', 'knowledge_artifacts', ['created_at'])
    op.create_index('ix_ka_project_status', 'knowledge_artifacts', ['project_id', 'status'])
    
    # Create published_knowledge table
    op.create_table(
        'published_knowledge',
        sa.Column('id', sa.String(255), nullable=False),
        sa.Column('project_id', sa.String(255), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('approval_status', sa.String(50), nullable=False),
        sa.Column('approved_by', sa.String(255), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_pk_project_id', 'published_knowledge', ['project_id'])
    op.create_index('ix_pk_approval_status', 'published_knowledge', ['approval_status'])
    op.create_index('ix_pk_created_at', 'published_knowledge', ['created_at'])
    
    # Create evaluation_executions table
    op.create_table(
        'evaluation_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', sa.String(255), nullable=False),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.Enum('pending', 'running', 'evaluating', 'iterating', 'completed', 'failed', 'cancelled', name='executionstatusenum'), nullable=False),
        sa.Column('configuration', sa.String(50), nullable=False),
        sa.Column('quality_threshold', sa.Float(), nullable=False),
        sa.Column('max_iterations', sa.Integer(), nullable=False),
        sa.Column('current_iteration', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=False),
        sa.Column('final_score', sa.Float(), nullable=True),
        sa.Column('final_decision', sa.String(50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('total_artifacts', sa.Integer(), nullable=False),
        sa.Column('artifacts_passed', sa.Integer(), nullable=False),
        sa.Column('artifacts_failed', sa.Integer(), nullable=False),
        sa.Column('iterations_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('final_scorecard', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('artifact_details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ee_project_id', 'evaluation_executions', ['project_id'])
    op.create_index('ix_ee_event_id', 'evaluation_executions', ['event_id'])
    op.create_index('ix_ee_status', 'evaluation_executions', ['status'])
    op.create_index('ix_ee_created_at', 'evaluation_executions', ['created_at'])
    op.create_index('ix_ee_project_status', 'evaluation_executions', ['project_id', 'status'])


def downgrade():
    """Drop all tables."""
    op.drop_index('ix_ee_project_status', table_name='evaluation_executions')
    op.drop_index('ix_ee_created_at', table_name='evaluation_executions')
    op.drop_index('ix_ee_status', table_name='evaluation_executions')
    op.drop_index('ix_ee_event_id', table_name='evaluation_executions')
    op.drop_index('ix_ee_project_id', table_name='evaluation_executions')
    op.drop_table('evaluation_executions')
    op.drop_index('ix_pk_created_at', table_name='published_knowledge')
    op.drop_index('ix_pk_approval_status', table_name='published_knowledge')
    op.drop_index('ix_pk_project_id', table_name='published_knowledge')
    op.drop_table('published_knowledge')
    op.drop_index('ix_ka_project_status', table_name='knowledge_artifacts')
    op.drop_index('ix_ka_created_at', table_name='knowledge_artifacts')
    op.drop_index('ix_ka_type', table_name='knowledge_artifacts')
    op.drop_index('ix_ka_status', table_name='knowledge_artifacts')
    op.drop_index('ix_ka_project_id', table_name='knowledge_artifacts')
    op.drop_table('knowledge_artifacts')
    op.drop_index('ix_projects_event_id_status', table_name='projects')
    op.drop_index('ix_projects_created_at', table_name='projects')
    op.drop_index('ix_projects_status', table_name='projects')
    op.drop_index('ix_projects_event_id', table_name='projects')
    op.drop_table('projects')
    op.drop_index('ix_sessions_created_at', table_name='sessions')
    op.drop_index('ix_sessions_event_id', table_name='sessions')
    op.drop_table('sessions')
    op.drop_index('ix_events_created_at', table_name='events')
    op.drop_index('ix_events_display_name', table_name='events')
    op.drop_table('events')
