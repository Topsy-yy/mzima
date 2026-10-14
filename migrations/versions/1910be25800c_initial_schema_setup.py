"""Initial schema setup.

Revision ID: 1910be25800c
Revises:
Create Date: 2026-10-13 04:57:01.946617
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "1910be25800c"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "appointment_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("patient_identifier", sa.String(length=100), nullable=False),
        sa.Column("requested_specialty", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("CLERK", "NURSE", "SHIFT_LEAD", "ADMIN", name="roleenum"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)
    op.create_table(
        "visits",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("token_number", sa.String(length=20), nullable=False),
        sa.Column("arrival_time", sa.DateTime(), nullable=False),
        sa.Column("age_band", sa.String(length=20), nullable=False),
        sa.Column("visit_type", sa.String(length=20), nullable=False),
        sa.Column("is_fast_track", sa.Boolean(), nullable=True),
        sa.Column("red_flags", sa.JSON(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("IN_QUEUE", "CALLED", "TRIAGED", "LEFT_UNSEEN", name="visitstatusenum"),
            nullable=True,
        ),
        sa.Column("triage_start_time", sa.DateTime(), nullable=True),
        sa.Column("triage_end_time", sa.DateTime(), nullable=True),
        sa.Column("triage_category", sa.String(length=20), nullable=True),
        sa.Column("destination", sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_visits_arrival_time"), "visits", ["arrival_time"], unique=False)
    op.create_index(op.f("ix_visits_is_fast_track"), "visits", ["is_fast_track"], unique=False)
    op.create_index(op.f("ix_visits_status"), "visits", ["status"], unique=False)
    op.create_index(op.f("ix_visits_token_number"), "visits", ["token_number"], unique=False)
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.String(length=100), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_events_timestamp"), "audit_events", ["timestamp"], unique=False)
    op.create_table(
        "clinician_decisions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("request_id", sa.Uuid(), nullable=False),
        sa.Column("clinician_id", sa.Uuid(), nullable=False),
        sa.Column("decision", sa.String(length=50), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["clinician_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["request_id"], ["appointment_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "queue_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("visit_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("reason_code", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["visit_id"], ["visits.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_queue_events_timestamp"), "queue_events", ["timestamp"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_queue_events_timestamp"), table_name="queue_events")
    op.drop_table("queue_events")
    op.drop_table("clinician_decisions")
    op.drop_index(op.f("ix_audit_events_timestamp"), table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index(op.f("ix_visits_token_number"), table_name="visits")
    op.drop_index(op.f("ix_visits_status"), table_name="visits")
    op.drop_index(op.f("ix_visits_is_fast_track"), table_name="visits")
    op.drop_index(op.f("ix_visits_arrival_time"), table_name="visits")
    op.drop_table("visits")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_table("users")
    op.drop_table("appointment_requests")
