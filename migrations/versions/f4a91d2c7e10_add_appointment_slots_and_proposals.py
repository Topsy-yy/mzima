"""Add appointment slots and proposal fields.

Revision ID: f4a91d2c7e10
Revises: d5105f93ed08
Create Date: 2026-10-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f4a91d2c7e10"
down_revision: Union[str, Sequence[str], None] = "d5105f93ed08"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "appointment_slots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("specialty", sa.String(length=100), nullable=False),
        sa.Column("starts_at", sa.DateTime(), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("booked_count", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_appointment_slots_specialty"), "appointment_slots", ["specialty"], unique=False
    )
    op.create_index(
        op.f("ix_appointment_slots_starts_at"), "appointment_slots", ["starts_at"], unique=False
    )
    with op.batch_alter_table("appointment_requests") as batch_op:
        batch_op.add_column(sa.Column("proposed_slot_id", sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column("booked_slot_id", sa.Uuid(), nullable=True))
        batch_op.add_column(
            sa.Column("agent_proposal", sa.JSON(), nullable=False, server_default="{}")
        )
        batch_op.create_foreign_key(
            "fk_appointment_requests_proposed_slot_id",
            "appointment_slots",
            ["proposed_slot_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_appointment_requests_booked_slot_id",
            "appointment_slots",
            ["booked_slot_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("appointment_requests") as batch_op:
        batch_op.drop_constraint(
            "fk_appointment_requests_booked_slot_id", type_="foreignkey"
        )
        batch_op.drop_constraint(
            "fk_appointment_requests_proposed_slot_id", type_="foreignkey"
        )
        batch_op.drop_column("agent_proposal")
        batch_op.drop_column("booked_slot_id")
        batch_op.drop_column("proposed_slot_id")
    op.drop_index(op.f("ix_appointment_slots_starts_at"), table_name="appointment_slots")
    op.drop_index(op.f("ix_appointment_slots_specialty"), table_name="appointment_slots")
    op.drop_table("appointment_slots")
