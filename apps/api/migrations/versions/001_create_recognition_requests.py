"""create recognition_requests

Revision ID: 001
Revises:
Create Date: 2026-06-23
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

recognition_status = postgresql.ENUM(
    "NOT_STARTED",
    "PENDING",
    "COMPLETED",
    "NEEDS_REVIEW",
    "FAILED",
    name="recognition_status",
    create_type=True,
)


def upgrade() -> None:
    recognition_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "recognition_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("image_url", sa.String(512), nullable=False),
        sa.Column("plate_number", sa.String(32), nullable=True),
        sa.Column("status", recognition_status, nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_recognition_requests_created_at_desc",
        "recognition_requests",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_recognition_requests_created_at_desc", table_name="recognition_requests")
    op.drop_table("recognition_requests")
    recognition_status.drop(op.get_bind(), checkfirst=True)
