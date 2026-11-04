from backend.adapters.clinic.mock_fhir import MockClinicFHIRAdapter
from backend.mcp.server import ReadOnlyMzimaMCP
from backend.models.domain import AppointmentRequest


def run_tests():
    print("=== Testing Mock FHIR Adapter ===")
    dummy_req = AppointmentRequest(
        patient_identifier="P-99201",
        requested_specialty="Pediatrics",
        status="APPROVED",
    )
    fhir_output = MockClinicFHIRAdapter.export_to_fhir_appointment(dummy_req)
    print(fhir_output)

    print("\n=== Testing Read-Only MCP Tools ===")
    print("Queue Summary:")
    print(ReadOnlyMzimaMCP.get_live_queue_summary())

    print("\nPending Reviews:")
    print(ReadOnlyMzimaMCP.get_pending_appointment_reviews())


if __name__ == "__main__":
    run_tests()