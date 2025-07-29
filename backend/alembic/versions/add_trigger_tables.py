"""Add trigger tables

Revision ID: trigger_tables_001
Revises: 068920cafe8f
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'trigger_tables_001'
down_revision = '068920cafe8f'
branch_labels = None
depends_on = None


def upgrade():
    # Create triggers table
    op.create_table('triggers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'PAUSED', name='triggerstatus'), nullable=False),
        sa.Column('conditions', sa.JSON(), nullable=False),
        sa.Column('action_type', sa.Enum('NOTIFY', 'CREATE_TASK', 'SEND_MESSAGE', 'WEBHOOK', name='triggeraction'), nullable=False),
        sa.Column('action_config', sa.JSON(), nullable=True),
        sa.Column('check_interval_minutes', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trigger_count', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_triggers_id'), 'triggers', ['id'], unique=False)
    op.create_index(op.f('ix_triggers_name'), 'triggers', ['name'], unique=False)

    # Create trigger_logs table
    op.create_table('trigger_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('trigger_id', sa.Integer(), nullable=False),
        sa.Column('triggered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('trigger_data', sa.JSON(), nullable=True),
        sa.Column('action_result', sa.JSON(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['trigger_id'], ['triggers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_trigger_logs_id'), 'trigger_logs', ['id'], unique=False)
    op.create_index(op.f('ix_trigger_logs_trigger_id'), 'trigger_logs', ['trigger_id'], unique=False)


def downgrade():
    # Drop trigger_logs table
    op.drop_index(op.f('ix_trigger_logs_trigger_id'), table_name='trigger_logs')
    op.drop_index(op.f('ix_trigger_logs_id'), table_name='trigger_logs')
    op.drop_table('trigger_logs')
    
    # Drop triggers table
    op.drop_index(op.f('ix_triggers_name'), table_name='triggers')
    op.drop_index(op.f('ix_triggers_id'), table_name='triggers')
    op.drop_table('triggers')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS triggeraction')
    op.execute('DROP TYPE IF EXISTS triggerstatus') 