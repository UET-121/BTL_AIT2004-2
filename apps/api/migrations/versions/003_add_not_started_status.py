"""add NOT_STARTED status (no-op — already in enum from 001)

Revision ID: 003
Revises: 002
Create Date: 2026-07-21
"""

from typing import Sequence, Union

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
