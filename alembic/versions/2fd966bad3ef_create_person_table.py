"""Create person table

Revision ID: 2fd966bad3ef
Revises:
Create Date: 2025-07-08 13:34:23.451111

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2fd966bad3ef'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - SQLite only."""
    # Create people table for SQLite
    op.create_table(
        'people',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('login_id', sa.String(), nullable=False, server_default='', unique=True),
        sa.Column('person_id', sa.String(), nullable=False, server_default='', unique=True),
        sa.Column('name_first', sa.String(), nullable=False, server_default=''),
        sa.Column('name_middle', sa.String(), nullable=False, server_default=''),
        sa.Column('name_last', sa.String(), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.current_timestamp()),
    )

    # SQLite trigger for updating updated_at
    op.execute("""
        CREATE TRIGGER update_people_updated_at
        AFTER UPDATE ON people
        FOR EACH ROW
        BEGIN
            UPDATE people SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END;
    """)

    op.create_index('ix_people_mayo_login_id', 'people', ['login_id'])
    op.create_index('ix_people_mayo_person_id', 'people', ['person_id'])


def downgrade() -> None:
    """Downgrade schema - SQLite only."""
    op.execute('DROP TRIGGER IF EXISTS update_people_updated_at')
    op.drop_index('ix_people_mayo_person_id', table_name='people')
    op.drop_index('ix_people_mayo_login_id', table_name='people')
    op.drop_table('people')
