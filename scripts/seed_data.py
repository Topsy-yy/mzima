import secrets
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.domain import (
    AppointmentRequest,
    RoleEnum,
    User,
    Visit,
    VisitStatusEnum,
)


DEMO_ACCOUNTS = (
    ("demo-clerk", RoleEnum.CLERK),
    ("demo-nurse", RoleEnum.NURSE),
    ("demo-clinician", RoleEnum.SHIFT_LEAD),
    ("demo-admin", RoleEnum.ADMIN),
)


def seed_demo_data() -> None:
    if not settings.DATABASE_URL.startswith("sqlite"):
        raise RuntimeError("Synthetic demo seeding is restricted to a local SQLite database.")

    db: Session = SessionLocal()
    credentials: list[tuple[str, str]] = []
    try:
        for username, role in DEMO_ACCOUNTS:
            if db.query(User).filter(User.username == username).first():
                continue
            password = secrets.token_urlsafe(18)
            db.add(
                User(
                    username=username,
                    hashed_password=get_password_hash(password),
                    role=role,
                    is_active=True,
                )
            )
            credentials.append((username, password))

        if db.query(AppointmentRequest).count() == 0:
            db.add_all(
                [
                    AppointmentRequest(
                        patient_identifier="DEMO-REQUEST-001",
                        requested_specialty="General outpatient",
                        status="PENDING_REVIEW",
                    ),
                    AppointmentRequest(
                        patient_identifier="DEMO-REQUEST-002",
                        requested_specialty="Chronic care review",
                        status="PENDING_REVIEW",
                    ),
                ]
            )

        if db.query(Visit).count() == 0:
            db.add(
                Visit(
                    token_number="T-001",
                    arrival_time=datetime.utcnow() - timedelta(minutes=18),
                    age_band="adult",
                    visit_type="new",
                    is_fast_track=False,
                    red_flags={},
                    status=VisitStatusEnum.IN_QUEUE,
                )
            )

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    if credentials:
        print("Generated local demo accounts (credentials shown only once):")
        for username, password in credentials:
            print(f"  {username}: {password}")
    else:
        print("Demo accounts already exist; no credentials were changed.")
    print("Seeded demo request and walk-in records only when their tables were empty.")


if __name__ == "__main__":
    seed_demo_data()
