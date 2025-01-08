"""added is_active field in company model

Revision ID: a4fbf7ec4f56
Revises: ebee5e41b91b
Create Date: 2025-01-06 13:09:40.015334

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a4fbf7ec4f56'
down_revision: Union[str, None] = 'ebee5e41b91b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('companies', sa.Column('is_active', sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column('companies', 'is_active')
