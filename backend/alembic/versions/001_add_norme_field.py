"""Add norme field to projets and update calculs norme type

Revision ID: 001_add_norme
Revises:
Create Date: 2026-01-20

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_add_norme'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create NormeType enum
    normetype_enum = sa.Enum(
        'EC2', 'ACI318', 'BAEL91', 'BS8110', 'CSA_A23',
        name='normetype'
    )

    # Add norme column to projets table
    op.add_column(
        'projets',
        sa.Column(
            'norme',
            normetype_enum,
            nullable=False,
            server_default='EC2'
        )
    )

    # For calculs table, the norme column already exists as VARCHAR
    # We need to convert it to the enum type
    # First, update any existing values to match enum format
    op.execute("UPDATE calculs SET norme = 'EC2' WHERE norme IS NULL OR norme = ''")
    op.execute("UPDATE calculs SET norme = 'EC2' WHERE norme NOT IN ('EC2', 'ACI318', 'BAEL91', 'BS8110', 'CSA_A23')")

    # Note: SQLite doesn't support ALTER COLUMN TYPE directly
    # For production PostgreSQL, you would do:
    # op.alter_column('calculs', 'norme', type_=normetype_enum, existing_type=sa.String(50))


def downgrade():
    # Remove norme column from projets
    op.drop_column('projets', 'norme')

    # Note: For PostgreSQL, you would also need to drop the enum type
    # op.execute("DROP TYPE IF EXISTS normetype")
