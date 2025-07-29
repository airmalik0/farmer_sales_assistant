"""Add task trigger fields

Revision ID: task_trigger_fields
Revises: trigger_tables_001
Create Date: 2024-01-01 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'task_trigger_fields'
down_revision = 'trigger_tables_001'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to tasks table
    op.add_column('tasks', sa.Column('source', sa.String(length=50), nullable=False, server_default='manual'))
    op.add_column('tasks', sa.Column('trigger_id', sa.Integer(), nullable=True))
    op.add_column('tasks', sa.Column('extra_data', sa.JSON(), nullable=True))
    op.add_column('tasks', sa.Column('telegram_notification_sent', sa.Boolean(), nullable=False, server_default='false'))
    
    # Add foreign key constraint
    op.create_foreign_key('fk_tasks_trigger_id', 'tasks', 'triggers', ['trigger_id'], ['id'])


def downgrade():
    # Drop foreign key constraint
    op.drop_constraint('fk_tasks_trigger_id', 'tasks', type_='foreignkey')
    
    # Drop new columns
    op.drop_column('tasks', 'telegram_notification_sent')
    op.drop_column('tasks', 'extra_data')
    op.drop_column('tasks', 'trigger_id')
    op.drop_column('tasks', 'source') 