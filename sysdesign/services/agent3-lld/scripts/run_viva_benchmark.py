import sys
import os

# Ensure current service directory is on python path
service_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if service_dir not in sys.path:
    sys.path.insert(0, service_dir)

from Controllers.umlController import UMLController
from schemas.umlSchema import GenerateRequest, HighLevelArchitecture, FunctionalRequirement

def run_benchmark():
    print("============================================================")
    print("EXECUTING RESEARCH VIVA BENCHMARK EVALUATION (case_001)")
    print("============================================================")

    payload = GenerateRequest(
        project_name="Healthcare Appointment System",
        project_description="Patient and Doctor Appointment Booking System",
        high_level_architecture=HighLevelArchitecture(
            pattern="Microservices",
            layers=[],
            architectural_constraints=[]
        ),
        functional_requirements=[
            FunctionalRequirement(
                id="REQ-001",
                title="Book Appointment",
                description="A patient can book an appointment with a doctor."
            ),
            FunctionalRequirement(
                id="REQ-002",
                title="View Appointments",
                description="A doctor can view scheduled appointments."
            )
        ],
        export_formats=["png"]
    )

    result = UMLController.generate(payload)
    print("\n[SUCCESS] Benchmark Execution Completed Successfully.")
    return result

if __name__ == "__main__":
    run_benchmark()
