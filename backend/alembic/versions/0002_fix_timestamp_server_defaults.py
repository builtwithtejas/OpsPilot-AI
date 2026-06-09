# backend/alembic/versions/0002_fix_timestamp_server_defaults.py

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Fix created_at and updated_at on incidents to have server-side defaults
    # so Postgres never receives a null for these columns.
    op.alter_column(
        "incidents", "created_at",
        type_=sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        existing_nullable=False,
    )
    op.alter_column(
        "incidents", "updated_at",
        type_=sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        existing_nullable=False,
    )
    # Apply the same fix to audit_logs while we're here
    op.alter_column(
        "audit_logs", "created_at",
        type_=sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        existing_nullable=False,
    )
    # And deployments and monitored_projects for consistency
    op.alter_column(
        "deployments", "created_at",
        type_=sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        existing_nullable=False,
    )
    op.alter_column(
        "monitored_projects", "created_at",
        type_=sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        existing_nullable=False,
    )


def downgrade() -> None:
    for table in ("incidents", "audit_logs", "deployments", "monitored_projects"):
        col = "created_at"
        op.alter_column(table, col, server_default=None, existing_nullable=False)
    op.alter_column("incidents", "updated_at", server_default=None, existing_nullable=False)