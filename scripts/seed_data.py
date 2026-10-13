import random
from datetime import datetime, timedelta
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.domain import RoleEnum, User, Visit, VisitStatusEnum

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def seed():
    db: Session = SessionLocal()
    try:
        # 1. Seed Users
        if not db.query(User).filter(User.username == "clerk1").first():
            clerk = User(
                username="clerk1",
                hashed_password=pwd_context.hash("clerkpass123"),
                role=RoleEnum.CLERK,
            )
            nurse = User(
                username="nurse1",
                hashed_password=pwd_context.hash("nursepass123"),
                role=RoleEnum.NURSE,
            )
            lead = User(
                username="lead1",
                hashed_password=pwd_context.hash("leadpass123"),
                role=RoleEnum.SHIFT_LEAD,
            )
            db.add_all([clerk, nurse, lead])
            db.commit()
            print("Seeded default users: clerk1, nurse1, lead1")

        # 2. Seed Synthetic Visits (Last 7 days)
        if db.query(Visit).count() == 0:
            now = datetime.utcnow()
            age_bands = ["under_5", "adult", "over_65"]
            visit_types = ["new", "review", "refill"]
            
            visits = []
            token_count = 100
            
            for day in range(7, 0, -1):
                base_time = now - timedelta(days=day)
                # Simulate morning rush hour (8 AM - 12 PM)
                for hour in range(8, 13):
                    arrivals_this_hour = random.randint(5, 12)
                    for _ in range(arrivals_this_hour):
                        token_count += 1
                        arrival_time = base_time.replace(
                            hour=hour,
                            minute=random.randint(0, 59),
                            second=random.randint(0, 59)
                        )
                        is_fast_track = random.random() < 0.10  # 10% fast-track
                        
                        visit = Visit(
                            token_number=f"T-{token_count}",
                            arrival_time=arrival_time,
                            age_band=random.choice(age_bands),
                            visit_type=random.choice(visit_types),
                            is_fast_track=is_fast_track,
                            red_flags={"breathing_difficulty": True} if is_fast_track else {},
                            status=VisitStatusEnum.TRIAGED,
                            triage_start_time=arrival_time + timedelta(minutes=random.randint(5, 25)),
                            triage_end_time=arrival_time + timedelta(minutes=random.randint(26, 35)),
                            triage_category=random.choice(["Green", "Yellow", "Red"]),
                            destination="Consultation",
                        )
                        visits.append(visit)
            
            db.bulk_save_objects(visits)
            db.commit()
            print(f"Seeded {len(visits)} synthetic visits across past 7 days.")

    finally:
        db.close()


if __name__ == "__main__":
    seed()