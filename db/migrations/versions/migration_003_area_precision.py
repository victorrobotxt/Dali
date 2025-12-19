"""fix_area_precision

Revision ID: 003
Revises: 002
Create Date: 2025-12-19 20:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Alter Listings Table
    op.alter_column('listings', 'advertised_area_sqm',
               existing_type=sa.Float(),
               type_=sa.Numeric(precision=10, scale=2),
               postgresql_using='advertised_area_sqm::numeric',
               existing_nullable=True)

def downgrade() -> None:
    op.alter_column('listings', 'advertised_area_sqm',
               existing_type=sa.Numeric(precision=10, scale=2),
               type_=sa.Float(),
               existing_nullable=True)
