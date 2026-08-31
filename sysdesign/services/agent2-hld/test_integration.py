"""
HLA Agent — Integration Test
Tests the full pipeline without requiring live API calls.
"""

import sys
import json
import io
from pathlib import Path

# Reconfigure stdout/stderr for Windows console unicode support
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))

from config import INPUT_DIR, THRESHOLDS, WEIGHTS
from evaluation import evaluate_architecture
from evaluation.cas import rank_candidates
from output.report import generate_report
from output.plantuml_gen import generate_plantuml
from output.mermaid_gen import generate_mermaid
from output.radar import generate_radar_chart

print("=== HLA AGENT INTEGRATION TEST ===")

# Load sample input
sample_file = INPUT_DIR / "sample_food_delivery.json"
with open(sample_file, "r", encoding="utf-8") as f:
    requirements = json.load(f)
print(f"✅ Loaded sample: {requirements['project']}")

# Mock parsed architecture
mock_arch = {
    "architecture_style": "Layered Architecture",
    "pros_and_cons": "Good separation of concerns with clear layer boundaries.",
    "layers": [
        {"name": "Presentation Layer", "order": 1},
        {"name": "Application Layer", "order": 2},
        {"name": "Domain Layer", "order": 3},
        {"name": "Data Access Layer", "order": 4},
    ],
    "components": [
        {
            "name": "OrderApiGateway",
            "layer": "Presentation Layer",
            "boundary": "presentation",
            "element_type": "gateway",
            "responsibilities": ["Routes external HTTP requests", "Handles API rate limiting and authentication"],
            "provided_interfaces": ["POST /orders", "GET /orders/{id}"],
            "required_interfaces": ["OrderService"],
            "requirement_ids": ["FR-1"]
        },
        {
            "name": "OrderService",
            "layer": "Application Layer",
            "boundary": "business_logic",
            "element_type": "service",
            "responsibilities": ["Manages order lifecycle and status", "Coordinates payment and delivery service calls"],
            "provided_interfaces": ["OrderManagementAPI"],
            "required_interfaces": ["PaymentGatewayService", "OrderRepository"],
            "requirement_ids": ["FR-1", "FR-2"]
        },
        {
            "name": "PaymentGatewayService",
            "layer": "Application Layer",
            "boundary": "business_logic",
            "element_type": "service",
            "responsibilities": ["Integrates with external payment provider", "Processes transactions securely"],
            "provided_interfaces": ["PaymentAPI"],
            "required_interfaces": ["PaymentRepository"],
            "requirement_ids": ["FR-3"]
        },
        {
            "name": "DeliveryService",
            "layer": "Domain Layer",
            "boundary": "business_logic",
            "element_type": "service",
            "responsibilities": ["Assigns drivers to orders based on proximity", "Tracks real-time delivery status"],
            "provided_interfaces": ["DeliveryTrackingAPI"],
            "required_interfaces": ["DeliveryRepository"],
            "requirement_ids": ["FR-4"]
        },
        {
            "name": "OrderRepository",
            "layer": "Data Access Layer",
            "boundary": "data_access",
            "element_type": "repository",
            "responsibilities": ["Persists order state to database", "Provides transactional queries"],
            "provided_interfaces": ["OrderDataStore"],
            "required_interfaces": ["PostgreSQLDatabase"],
            "requirement_ids": ["FR-1"]
        },
        {
            "name": "PaymentRepository",
            "layer": "Data Access Layer",
            "boundary": "data_access",
            "element_type": "repository",
            "responsibilities": ["Persists payment transactions", "Stores audit records securely"],
            "provided_interfaces": ["PaymentDataStore"],
            "required_interfaces": ["PostgreSQLDatabase"],
            "requirement_ids": ["FR-3"]
        },
        {
            "name": "DeliveryRepository",
            "layer": "Data Access Layer",
            "boundary": "data_access",
            "element_type": "repository",
            "responsibilities": ["Persists driver locations and routes", "Stores delivery history"],
            "provided_interfaces": ["DeliveryDataStore"],
            "required_interfaces": ["PostgreSQLDatabase"],
            "requirement_ids": ["FR-4"]
        },
        {
            "name": "NotificationHandler",
            "layer": "Application Layer",
            "boundary": "business_logic",
            "element_type": "handler",
            "responsibilities": ["Sends push notifications to mobile clients", "Dispatches email receipts"],
            "provided_interfaces": ["NotificationAPI"],
            "required_interfaces": ["FCMProvider"],
            "requirement_ids": ["FR-5"]
        }
    ],
    "connectors": [
        {"from_component": "OrderApiGateway", "to_component": "OrderService", "connector_type": "sync_call", "protocol": "REST"},
        {"from_component": "OrderService", "to_component": "PaymentGatewayService", "connector_type": "sync_call", "protocol": "gRPC"},
        {"from_component": "OrderService", "to_component": "OrderRepository", "connector_type": "sync_call", "protocol": "SQL"},
        {"from_component": "OrderService", "to_component": "NotificationHandler", "connector_type": "async_message", "protocol": "AMQP"},
        {"from_component": "PaymentGatewayService", "to_component": "PaymentRepository", "connector_type": "sync_call", "protocol": "SQL"},
        {"from_component": "DeliveryService", "to_component": "DeliveryRepository", "connector_type": "sync_call", "protocol": "SQL"},
    ]
}

# Test evaluation
scores = evaluate_architecture(mock_arch, requirements)
print(f"\n📊 EVALUATION RESULTS (6-Metric Framework):")
print(f"   Detected Style: {scores.get('detected_style')}")
print(f"   RTS  = {scores['RTS']:.4f}  (threshold: {THRESHOLDS['RTS']})")
print(f"   QAC  = {scores['QAC']:.4f}  (threshold: {THRESHOLDS['QAC']})")
print(f"   CI   = {scores['CI']:.4f}  (threshold: {THRESHOLDS['CI']})")
print(f"   CoS  = {scores['CoS']:.4f}  (threshold: {THRESHOLDS['CoS']})")
print(f"   SSM₁ ({scores['ssm1_name']}) = {scores['SSM1']:.4f}  (threshold: {THRESHOLDS['SSM1']})")
print(f"   SSM₂ ({scores['ssm2_name']}) = {scores['SSM2']:.4f}  (threshold: {THRESHOLDS['SSM2']})")
print(f"   ─────────────────────")
print(f"   CAS  = {scores['CAS']:.4f}  (threshold: {THRESHOLDS['CAS']})")
print(f"   Verdict: {scores['verdict']}")

# Test ranking with 2 mock candidates
candidates = [
    {"model": "meta-llama/llama-3.1-8b-instruct:free", "candidate_num": 1, "architecture": mock_arch, "scores": scores},
    {"model": "qwen/qwen-2.5-7b-instruct:free", "candidate_num": 1, "architecture": mock_arch,
     "scores": {**scores, "CAS": scores["CAS"] - 0.05, "RTS": scores["RTS"] - 0.1}},
]
ranked = rank_candidates(candidates)
print(f"\n🏆 Ranking: {[(c['rank'], c['model'], c['scores']['CAS']) for c in ranked]}")

# Test output generators
report = generate_report(ranked, requirements, "TEST01")
print(f"\n✅ Report generated: {len(report)} chars")

puml = generate_plantuml(mock_arch, "Food Delivery")
print(f"✅ PlantUML generated: {len(puml)} chars")

mmd = generate_mermaid(mock_arch, "Food Delivery")
print(f"✅ Mermaid generated: {len(mmd)} chars")

# Test radar chart
from config import RESULTS_DIR
radar_path = str(RESULTS_DIR / "test_radar.png")
generate_radar_chart(ranked, radar_path, "Test Radar")
print(f"✅ Radar chart generated: {radar_path}")

print("\n🎉 INTEGRATION TEST COMPLETED SUCCESSFULLY!")
