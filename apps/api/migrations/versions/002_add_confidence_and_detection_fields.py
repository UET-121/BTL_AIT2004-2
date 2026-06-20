"""add confidence and detection fields

Revision ID: 002
Revises: 001
Create Date: 2026-07-21
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("recognition_requests", sa.Column("confidence_score", sa.Float(), nullable=True))
    op.add_column(
        "recognition_requests", sa.Column("detection_confidence", sa.Float(), nullable=True)
    )
    op.add_column("recognition_requests", sa.Column("ocr_confidence", sa.Float(), nullable=True))
    op.add_column(
        "recognition_requests",
        sa.Column("needs_review", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "recognition_requests",
        sa.Column("bounding_box", postgresql.JSON(astext_type=sa.Text()), nullable=True),
    )
    op.add_column("recognition_requests", sa.Column("plate_region", sa.String(8), nullable=True))
    op.add_column(
        "recognition_requests",
        sa.Column("metadata_json", postgresql.JSON(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("recognition_requests", "metadata_json")
    op.drop_column("recognition_requests", "plate_region")
    op.drop_column("recognition_requests", "bounding_box")
    op.drop_column("recognition_requests", "needs_review")
    op.drop_column("recognition_requests", "ocr_confidence")
    op.drop_column("recognition_requests", "detection_confidence")
    op.drop_column("recognition_requests", "confidence_score")
