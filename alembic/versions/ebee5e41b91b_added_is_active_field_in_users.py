"""added is_active field in users

Revision ID: ebee5e41b91b
Revises: 71650d62e13d
Create Date: 2025-01-06 10:23:58.255679

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ebee5e41b91b'
down_revision: Union[str, None] = '71650d62e13d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=True))
    


def downgrade() -> None:
    op.drop_column('users', 'is_active')

