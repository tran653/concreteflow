"""add type_poutrelle to cahiers_portees

Revision ID: 002_add_type_poutrelle
Revises: 001_add_norme_field
Create Date: 2024-01-22

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_type_poutrelle'
down_revision = '001_add_norme'
branch_labels = None
depends_on = None


def upgrade():
    # Add type_poutrelle column to cahiers_portees table
    op.add_column('cahiers_portees', sa.Column('type_poutrelle', sa.String(50), nullable=True, server_default='precontrainte'))

    # Update existing rows to have default value
    op.execute("UPDATE cahiers_portees SET type_poutrelle = 'precontrainte' WHERE type_poutrelle IS NULL")


def downgrade():
    op.drop_column('cahiers_portees', 'type_poutrelle')
