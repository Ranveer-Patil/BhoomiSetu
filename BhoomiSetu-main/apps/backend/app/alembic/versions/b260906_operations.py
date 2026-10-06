"""Operational records, deadlines and per-user inbox receipts.

Existing records are preserved. Unknown historic timestamps remain NULL.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "b260906_operations"
down_revision = "a4e38234aa24"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("locale", sa.String(10), nullable=False, server_default="en"))
    op.add_column(
        "cases",
        sa.Column("displaced_family_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_check_constraint(
        "ck_case_families",
        "cases",
        "affected_family_count >= 0 AND displaced_family_count >= 0 "
        "AND displaced_family_count <= affected_family_count",
    )
    op.add_column(
        "documents",
        sa.Column("document_type", sa.String(50), nullable=False, server_default="land_record"),
    )
    op.add_column("documents", sa.Column("created_at", sa.DateTime(timezone=True)))
    for name in ("description", "response"):
        op.add_column("grievances", sa.Column(name, sa.Text()))
    op.add_column("grievances", sa.Column("created_at", sa.DateTime(timezone=True)))
    for name in ("assessed_amount", "disbursed_amount"):
        op.add_column("compensation_status", sa.Column(name, sa.Numeric(16, 2)))
    op.add_column("compensation_status", sa.Column("due_date", sa.Date()))
    op.add_column(
        "compensation_status",
        sa.Column("reference", sa.String(500), nullable=False, server_default=""),
    )
    op.add_column("compensation_status", sa.Column("updated_at", sa.DateTime(timezone=True)))
    op.create_check_constraint(
        "ck_compensation_amounts",
        "compensation_status",
        "assessed_amount >= 0 AND disbursed_amount >= 0 AND "
        "(disbursed_amount IS NULL OR (assessed_amount IS NOT NULL "
        "AND disbursed_amount <= assessed_amount))",
    )
    op.add_column(
        "rr_status",
        sa.Column("families_supported", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "rr_status", sa.Column("notes", sa.String(500), nullable=False, server_default="")
    )
    op.add_column("rr_status", sa.Column("updated_at", sa.DateTime(timezone=True)))
    op.create_check_constraint("ck_rr_families", "rr_status", "families_supported >= 0")
    op.create_table(
        "case_deadlines",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "case_id", sa.Uuid(), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("stage", postgresql.ENUM(name="case_stage", create_type=False), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("basis", sa.String(30), nullable=False),
        sa.Column("reference", sa.String(500), nullable=False),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_case_deadlines_case_id", "case_deadlines", ["case_id"])
    op.create_table(
        "alert_receipts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("alert_key", sa.String(200), nullable=False),
        sa.Column(
            "read_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("user_id", "alert_key"),
    )


def downgrade() -> None:
    op.drop_table("alert_receipts")
    op.drop_table("case_deadlines")
    op.drop_constraint("ck_case_families", "cases", type_="check")
    op.drop_constraint("ck_compensation_amounts", "compensation_status", type_="check")
    op.drop_constraint("ck_rr_families", "rr_status", type_="check")
    for table, columns in {
        "users": ["locale"],
        "cases": ["displaced_family_count"],
        "documents": ["document_type", "created_at"],
        "grievances": ["description", "response", "created_at"],
        "compensation_status": [
            "assessed_amount",
            "disbursed_amount",
            "due_date",
            "reference",
            "updated_at",
        ],
        "rr_status": ["families_supported", "notes", "updated_at"],
    }.items():
        for name in columns:
            op.drop_column(table, name)
