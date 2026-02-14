"""Marketplace schema

Revision ID: 0001_marketplace
Revises:
Create Date: 2026-02-14

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_marketplace"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "agents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("published_version_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agents_owner_id", "agents", ["owner_id"])
    op.create_index("ix_agents_slug", "agents", ["slug"], unique=True)
    op.create_index("ix_agents_status", "agents", ["status"])

    op.create_table(
        "agent_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("agent_id", sa.Integer(), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=False),
        sa.Column("max_steps", sa.Integer(), nullable=False),
        sa.Column("tool_names", sa.JSON(), nullable=False),
        sa.Column("memory_enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("agent_id", "version_number", name="uq_agent_version_number"),
    )
    op.create_index("ix_agent_versions_agent_id", "agent_versions", ["agent_id"])
    op.create_foreign_key(
        "fk_agents_published_version",
        "agents",
        "agent_versions",
        ["published_version_id"],
        ["id"],
    )

    op.create_table(
        "listings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("agent_id", sa.Integer(), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("version_id", sa.Integer(), sa.ForeignKey("agent_versions.id"), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("install_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_listings_agent_id", "listings", ["agent_id"], unique=True)
    op.create_index("ix_listings_slug", "listings", ["slug"], unique=True)
    op.create_index("ix_listings_category", "listings", ["category"])

    op.create_table(
        "installs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("listing_id", sa.Integer(), sa.ForeignKey("listings.id"), nullable=False),
        sa.Column("agent_id", sa.Integer(), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_installs_user_id", "installs", ["user_id"])
    op.create_index("ix_installs_listing_id", "installs", ["listing_id"])

    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("listing_id", sa.Integer(), sa.ForeignKey("listings.id"), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "listing_id", name="uq_review_user_listing"),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_reviews_rating"),
    )
    op.create_index("ix_reviews_listing_id", "reviews", ["listing_id"])

    op.create_table(
        "threads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("agent_id", sa.Integer(), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("version_id", sa.Integer(), sa.ForeignKey("agent_versions.id"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_threads_agent_id", "threads", ["agent_id"])
    op.create_index("ix_threads_user_id", "threads", ["user_id"])

    op.create_table(
        "runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("thread_id", sa.Integer(), sa.ForeignKey("threads.id"), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("user_message", sa.Text(), nullable=False),
        sa.Column("assistant_message", sa.Text(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("step_count", sa.Integer(), nullable=False),
        sa.Column("estimated_tokens", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_runs_thread_id", "runs", ["thread_id"])
    op.create_index("ix_runs_status", "runs", ["status"])

    op.create_table(
        "run_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column("node_name", sa.String(length=80), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_run_events_run_id", "run_events", ["run_id"])

    op.create_table(
        "test_suites",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("agent_id", sa.Integer(), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
    )
    op.create_index("ix_test_suites_agent_id", "test_suites", ["agent_id"])

    op.create_table(
        "test_cases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("suite_id", sa.Integer(), sa.ForeignKey("test_suites.id"), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("input_text", sa.Text(), nullable=False),
        sa.Column("expected_tool", sa.String(length=80), nullable=True),
        sa.Column("expected_phrase", sa.String(length=300), nullable=True),
    )
    op.create_index("ix_test_cases_suite_id", "test_cases", ["suite_id"])

    op.create_table(
        "test_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("suite_id", sa.Integer(), sa.ForeignKey("test_suites.id"), nullable=False),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("test_cases.id"), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_test_runs_case_id", "test_runs", ["case_id"])

    op.create_table(
        "notes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_notes_user_id", "notes", ["user_id"])

    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("knowledge_documents")
    op.drop_table("notes")
    op.drop_table("test_runs")
    op.drop_table("test_cases")
    op.drop_table("test_suites")
    op.drop_table("run_events")
    op.drop_table("runs")
    op.drop_table("threads")
    op.drop_table("reviews")
    op.drop_table("installs")
    op.drop_table("listings")
    op.drop_constraint("fk_agents_published_version", "agents", type_="foreignkey")
    op.drop_table("agent_versions")
    op.drop_table("agents")
    op.drop_table("users")
