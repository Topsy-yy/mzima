import uuid
from datetime import datetime, timedelta
from typing import Any

from app.models.domain import AppointmentRequest


class MockClinicFHIRAdapter:
    """Mock integration adapter mapping internal appointments to HL7 FHIR standards."""

    @staticmethod
    def export_to_fhir_appointment(
        app_request: AppointmentRequest,
        start_time: datetime | None = None,
    ) -> dict[str, Any]:
        """Converts an internal AppointmentRequest model into a FHIR Appointment resource."""
        booking_start = start_time or (datetime.utcnow() + timedelta(days=1))
        booking_end = booking_start + timedelta(minutes=30)

        fhir_resource = {
            "resourceType": "Appointment",
            "id": str(app_request.id),
            "status": "booked" if app_request.status == "APPROVED" else "proposed",
            "serviceCategory": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/service-category",
                            "display": app_request.requested_specialty,
                        }
                    ]
                }
            ],
            "start": booking_start.isoformat() + "Z",
            "end": booking_end.isoformat() + "Z",
            "participant": [
                {
                    "actor": {
                        "reference": f"Patient/{app_request.patient_identifier}",
                        "display": f"Patient {app_request.patient_identifier}",
                    },
                    "status": "accepted",
                }
            ],
            "comment": f"Synchronized from Mzima API. Status: {app_request.status}",
        }
        return fhir_resource