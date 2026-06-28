"""Add client message idempotency.

Revision ID: 002_message_idempotency
Revises: 001_relational_integrity
Create Date: 2026-06-28
"""

from alembic import op
import sqlalchemy as sa


revision = "002_message_idempotency"
down_revision = "001_relational_integrity"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "messages",
        sa.Column("client_id", sa.String(length=64), nullable=True),
    )
    op.create_unique_constraint(
        "uq_messages_sender_client",
        "messages",
        ["sender_id", "client_id"],
    )


def downgrade():
    op.drop_constraint(
        "uq_messages_sender_client",
        "messages",
        type_="unique",
    )
    op.drop_column("messages", "client_id")
