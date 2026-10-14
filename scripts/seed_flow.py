import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.db.session import SessionLocal
from app.services.flow.seeding import ensure_flow_reference_data

PDF_DIR = os.path.join(PROJECT_ROOT, "app")


def main():
    db = SessionLocal()
    try:
        result = ensure_flow_reference_data(db, PDF_DIR)
        print("Flow reference data seeded:", result)
    finally:
        db.close()


if __name__ == "__main__":
    main()
