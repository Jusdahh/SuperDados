"""initial anticontamination tables

Revision ID: 20260603_0001
Revises:
Create Date: 2026-06-03
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260603_0001"
down_revision = None
branch_labels = None
depends_on = None


json_type = postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "surveys",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("city", sa.String(length=120), nullable=False),
        sa.Column("state", sa.String(length=2), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("external_form_provider", sa.String(length=50), nullable=False),
        sa.Column("external_form_id", sa.String(length=120), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_surveys_id"), "surveys", ["id"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("before_json", json_type, nullable=True),
        sa.Column("after_json", json_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_entity_id"), "audit_logs", ["entity_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_type"), "audit_logs", ["entity_type"], unique=False)
    op.create_index(op.f("ix_audit_logs_id"), "audit_logs", ["id"], unique=False)

    op.create_table(
        "survey_invites",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("survey_id", sa.Integer(), nullable=False),
        sa.Column("external_token", sa.String(length=255), nullable=True),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("source_channel", sa.String(length=120), nullable=True),
        sa.Column("utm_source", sa.String(length=120), nullable=True),
        sa.Column("utm_campaign", sa.String(length=120), nullable=True),
        sa.Column("utm_content", sa.String(length=120), nullable=True),
        sa.Column("first_ip_hash", sa.String(length=64), nullable=True),
        sa.Column("first_device_hash", sa.String(length=64), nullable=True),
        sa.Column("first_user_agent_hash", sa.String(length=64), nullable=True),
        sa.Column("first_opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["survey_id"], ["surveys.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_survey_invites_id"), "survey_invites", ["id"], unique=False)
    op.create_index(op.f("ix_survey_invites_status"), "survey_invites", ["status"], unique=False)
    op.create_index(op.f("ix_survey_invites_survey_id"), "survey_invites", ["survey_id"], unique=False)
    op.create_index(op.f("ix_survey_invites_token_hash"), "survey_invites", ["token_hash"], unique=True)

    op.create_table(
        "responses_raw",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("survey_id", sa.Integer(), nullable=False),
        sa.Column("invite_id", sa.Integer(), nullable=False),
        sa.Column("external_response_id", sa.String(length=120), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("ip_hash", sa.String(length=64), nullable=True),
        sa.Column("device_hash", sa.String(length=64), nullable=True),
        sa.Column("user_agent_hash", sa.String(length=64), nullable=True),
        sa.Column("source_channel", sa.String(length=120), nullable=True),
        sa.Column("raw_payload", json_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["invite_id"], ["survey_invites.id"]),
        sa.ForeignKeyConstraint(["survey_id"], ["surveys.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_responses_raw_device_hash"), "responses_raw", ["device_hash"], unique=False)
    op.create_index(op.f("ix_responses_raw_id"), "responses_raw", ["id"], unique=False)
    op.create_index(op.f("ix_responses_raw_invite_id"), "responses_raw", ["invite_id"], unique=False)
    op.create_index(op.f("ix_responses_raw_ip_hash"), "responses_raw", ["ip_hash"], unique=False)
    op.create_index(op.f("ix_responses_raw_survey_id"), "responses_raw", ["survey_id"], unique=False)

    op.create_table(
        "response_validations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("response_raw_id", sa.Integer(), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("flags", json_type, nullable=False),
        sa.Column("reviewed_by", sa.String(length=120), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["response_raw_id"], ["responses_raw.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_response_validations_id"), "response_validations", ["id"], unique=False)
    op.create_index(op.f("ix_response_validations_response_raw_id"), "response_validations", ["response_raw_id"], unique=True)
    op.create_index(op.f("ix_response_validations_status"), "response_validations", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_response_validations_status"), table_name="response_validations")
    op.drop_index(op.f("ix_response_validations_response_raw_id"), table_name="response_validations")
    op.drop_index(op.f("ix_response_validations_id"), table_name="response_validations")
    op.drop_table("response_validations")
    op.drop_index(op.f("ix_responses_raw_survey_id"), table_name="responses_raw")
    op.drop_index(op.f("ix_responses_raw_ip_hash"), table_name="responses_raw")
    op.drop_index(op.f("ix_responses_raw_invite_id"), table_name="responses_raw")
    op.drop_index(op.f("ix_responses_raw_id"), table_name="responses_raw")
    op.drop_index(op.f("ix_responses_raw_device_hash"), table_name="responses_raw")
    op.drop_table("responses_raw")
    op.drop_index(op.f("ix_survey_invites_token_hash"), table_name="survey_invites")
    op.drop_index(op.f("ix_survey_invites_survey_id"), table_name="survey_invites")
    op.drop_index(op.f("ix_survey_invites_status"), table_name="survey_invites")
    op.drop_index(op.f("ix_survey_invites_id"), table_name="survey_invites")
    op.drop_table("survey_invites")
    op.drop_index(op.f("ix_audit_logs_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_entity_type"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_entity_id"), table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index(op.f("ix_surveys_id"), table_name="surveys")
    op.drop_table("surveys")
