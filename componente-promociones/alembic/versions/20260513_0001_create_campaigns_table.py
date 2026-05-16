"""create campaigns table

Revision ID: 20260513_0001
Revises:
Create Date: 2026-05-13 00:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260513_0001"
down_revision = None
branch_labels = None
depends_on = None


campaign_type_enum = sa.Enum(
    "NEXT_BEST_OFFER",
    "NEXT_BEST_ACTION",
    "DISCOUNT",
    "CROSS_SELL",
    "SUPPORT_OFFER",
    "DATA_PLAN_OFFER",
    name="campaign_type",
    native_enum=False,
)

campaign_status_enum = sa.Enum(
    "DRAFT",
    "ACTIVE",
    "PAUSED",
    "CANCELLED",
    "EXPIRED",
    name="campaign_status",
    native_enum=False,
)

campaign_channel_enum = sa.Enum(
    "WEB",
    "APP",
    "WHATSAPP",
    "PHONE",
    "CALL_CENTER",
    "ALL",
    name="campaign_channel",
    native_enum=False,
)


def upgrade() -> None:
    campaign_type_enum.create(op.get_bind(), checkfirst=True)
    campaign_status_enum.create(op.get_bind(), checkfirst=True)
    campaign_channel_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "campaigns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("type", campaign_type_enum, nullable=False),
        sa.Column("status", campaign_status_enum, nullable=False, server_default="DRAFT"),
        sa.Column("channel", campaign_channel_enum, nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("action_message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )


def downgrade() -> None:
    op.drop_table("campaigns")
    campaign_channel_enum.drop(op.get_bind(), checkfirst=True)
    campaign_status_enum.drop(op.get_bind(), checkfirst=True)
    campaign_type_enum.drop(op.get_bind(), checkfirst=True)
