"""
Research Experiment — Cross-Style Bias Validation

Evaluates the exact same requirement specification adapted into all 5 canonical styles:
1. Layered Architecture
2. Microservices Architecture
3. Event-Driven Architecture
4. Modular Monolith
5. Pipe-and-Filter Architecture

Demonstrates that SSM₁ and SSM₂ properly complement universal metrics (RTS, QAC, CI, CoS)
without unfairly penalizing inherently dense architecture styles (e.g. Microservices vs Layered).
"""

import sys
import json
import io
import logging
from pathlib import Path

# Reconfigure stdout for Windows console unicode support
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from evaluation import evaluate_architecture

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CrossStyle-Runner")


def run_cross_style_experiment(sample_file: str | None = None):
    """Run cross-style bias validation experiment across all 5 styles."""
    if not sample_file:
        sample_file = str(BASE_DIR / "input" / "sample_food_delivery.json")

    with open(sample_file, "r", encoding="utf-8") as f:
        requirements = json.load(f)

    # 5 Mock Architectures representing the 5 styles for the exact same system
    styles_mock = {
        "Layered": {
            "architecture_style": "Layered Architecture",
            "layers": [
                {"name": "Presentation Layer", "order": 1},
                {"name": "Application Layer", "order": 2},
                {"name": "Data Access Layer", "order": 3},
            ],
            "components": [
                {"name": "OrderApiGateway", "layer": "Presentation Layer", "responsibilities": ["Request routing", "Auth rate limiting"]},
                {"name": "OrderService", "layer": "Application Layer", "responsibilities": ["Order lifecycle management", "Status orchestration"]},
                {"name": "PaymentGatewayService", "layer": "Application Layer", "responsibilities": ["Payment integration", "Secure transactions"]},
                {"name": "DeliveryService", "layer": "Application Layer", "responsibilities": ["Proximity driver dispatch", "Realtime location tracking"]},
                {"name": "NotificationHandler", "layer": "Application Layer", "responsibilities": ["Push notification dispatches", "SMS receipt notifications"]},
                {"name": "OrderRepository", "layer": "Data Access Layer", "responsibilities": ["Order data persistence", "Transactional queries"]},
                {"name": "PaymentRepository", "layer": "Data Access Layer", "responsibilities": ["Payment ledger store", "Audit logging"]},
                {"name": "DeliveryRepository", "layer": "Data Access Layer", "responsibilities": ["GPS tracking persistence", "Driver route store"]},
            ],
            "connectors": [
                {"from_component": "OrderApiGateway", "to_component": "OrderService", "connector_type": "sync_call"},
                {"from_component": "OrderService", "to_component": "OrderRepository", "connector_type": "sync_call"},
                {"from_component": "OrderService", "to_component": "PaymentGatewayService", "connector_type": "sync_call"},
                {"from_component": "PaymentGatewayService", "to_component": "PaymentRepository", "connector_type": "sync_call"},
                {"from_component": "OrderService", "to_component": "DeliveryService", "connector_type": "sync_call"},
                {"from_component": "DeliveryService", "to_component": "DeliveryRepository", "connector_type": "sync_call"},
            ]
        },
        "Microservices": {
            "architecture_style": "Microservices Architecture",
            "components": [
                {"name": "ApiGateway", "boundary": "infrastructure", "provided_interfaces": ["HTTP"], "responsibilities": ["Request routing", "Token auth validation"]},
                {"name": "OrderMicroservice", "boundary": "business_logic", "provided_interfaces": ["OrderREST"], "responsibilities": ["Order lifecycle management", "State machine"]},
                {"name": "PaymentMicroservice", "boundary": "business_logic", "provided_interfaces": ["PaymentgRPC"], "responsibilities": ["Payment integration", "Transaction audit"]},
                {"name": "DeliveryMicroservice", "boundary": "business_logic", "provided_interfaces": ["DeliveryREST"], "responsibilities": ["Driver dispatch tracking", "Location mapping"]},
                {"name": "NotificationMicroservice", "boundary": "business_logic", "provided_interfaces": ["NotifyREST"], "responsibilities": ["Push notification dispatches", "SMS receipts"]},
                {"name": "OrderDatabase", "boundary": "data_access", "provided_interfaces": ["SQL"], "responsibilities": ["Order schema storage", "Persistence"]},
                {"name": "PaymentDatabase", "boundary": "data_access", "provided_interfaces": ["SQL"], "responsibilities": ["Payment audit ledger", "Secure storage"]},
                {"name": "DeliveryDatabase", "boundary": "data_access", "provided_interfaces": ["SpatialSQL"], "responsibilities": ["GPS route spatial index", "Location store"]},
            ],
            "connectors": [
                {"from_component": "ApiGateway", "to_component": "OrderMicroservice", "connector_type": "sync_call"},
                {"from_component": "ApiGateway", "to_component": "PaymentMicroservice", "connector_type": "sync_call"},
                {"from_component": "ApiGateway", "to_component": "DeliveryMicroservice", "connector_type": "sync_call"},
                {"from_component": "OrderMicroservice", "to_component": "OrderDatabase", "connector_type": "sync_call"},
                {"from_component": "PaymentMicroservice", "to_component": "PaymentDatabase", "connector_type": "sync_call"},
                {"from_component": "DeliveryMicroservice", "to_component": "DeliveryDatabase", "connector_type": "sync_call"},
            ]
        },
        "Event-Driven": {
            "architecture_style": "Event-Driven Architecture",
            "components": [
                {"name": "EventBroker", "boundary": "infrastructure", "responsibilities": ["Kafka message broker", "Topic partitioning"]},
                {"name": "OrderIngressService", "boundary": "presentation", "responsibilities": ["Receive HTTP order request", "Publish OrderCreated event"]},
                {"name": "PaymentProcessorHandler", "boundary": "business_logic", "responsibilities": ["Consume OrderCreated event", "Process payment charge"]},
                {"name": "DeliveryDispatcherHandler", "boundary": "business_logic", "responsibilities": ["Consume PaymentCleared event", "Dispatch driver proximity"]},
                {"name": "NotificationConsumer", "boundary": "business_logic", "responsibilities": ["Consume PaymentCleared event", "Send customer SMS notification"]},
                {"name": "AnalyticsConsumer", "boundary": "business_logic", "responsibilities": ["Consume all domain events", "Aggregate order metric stats"]},
                {"name": "OrderStateStore", "boundary": "data_access", "responsibilities": ["Order domain event store", "Persist event log"]},
                {"name": "PaymentLedgerStore", "boundary": "data_access", "responsibilities": ["Payment audit event store", "Persist audit log"]},
            ],
            "connectors": [
                {"from_component": "OrderIngressService", "to_component": "EventBroker", "connector_type": "event_publish"},
                {"from_component": "EventBroker", "to_component": "PaymentProcessorHandler", "connector_type": "async_message"},
                {"from_component": "EventBroker", "to_component": "DeliveryDispatcherHandler", "connector_type": "async_message"},
                {"from_component": "EventBroker", "to_component": "NotificationConsumer", "connector_type": "async_message"},
                {"from_component": "PaymentProcessorHandler", "to_component": "PaymentLedgerStore", "connector_type": "sync_call"},
                {"from_component": "OrderIngressService", "to_component": "OrderStateStore", "connector_type": "sync_call"},
            ]
        },
        "Modular Monolith": {
            "architecture_style": "Modular Monolith",
            "layers": [
                {"name": "OrderModule", "order": 1},
                {"name": "PaymentModule", "order": 1},
                {"name": "DeliveryModule", "order": 1},
            ],
            "components": [
                {"name": "OrderFacade", "layer": "OrderModule", "boundary": "presentation", "responsibilities": ["Order module public API", "Order lifecycle manager"]},
                {"name": "OrderInternalEngine", "layer": "OrderModule", "boundary": "business_logic", "responsibilities": ["Order validation calculation", "State transition logic"]},
                {"name": "PaymentFacade", "layer": "PaymentModule", "boundary": "presentation", "responsibilities": ["Payment module public API", "Payment charge coordinator"]},
                {"name": "PaymentInternalEngine", "layer": "PaymentModule", "boundary": "business_logic", "responsibilities": ["PCI compliance encryption", "Stripe API adapter"]},
                {"name": "DeliveryFacade", "layer": "DeliveryModule", "boundary": "presentation", "responsibilities": ["Delivery module public API", "Driver assignment coordinator"]},
                {"name": "DeliveryInternalEngine", "layer": "DeliveryModule", "boundary": "business_logic", "responsibilities": ["GPS Haversine distance", "Proximity algorithm"]},
                {"name": "SharedNotificationService", "layer": "SharedModule", "boundary": "infrastructure", "responsibilities": ["Push notification dispatches", "SMS receipt service"]},
                {"name": "SharedDatabaseAccess", "layer": "SharedModule", "boundary": "data_access", "responsibilities": ["Shared PostgreSQL pool", "ORMapping manager"]},
            ],
            "connectors": [
                {"from_component": "OrderFacade", "to_component": "OrderInternalEngine", "connector_type": "sync_call"},
                {"from_component": "OrderInternalEngine", "to_component": "PaymentFacade", "connector_type": "sync_call"},
                {"from_component": "PaymentFacade", "to_component": "PaymentInternalEngine", "connector_type": "sync_call"},
                {"from_component": "OrderInternalEngine", "to_component": "DeliveryFacade", "connector_type": "sync_call"},
                {"from_component": "DeliveryFacade", "to_component": "DeliveryInternalEngine", "connector_type": "sync_call"},
                {"from_component": "OrderInternalEngine", "to_component": "SharedNotificationService", "connector_type": "sync_call"},
            ]
        },
        "Pipe-and-Filter": {
            "architecture_style": "Pipe-and-Filter Architecture",
            "components": [
                {"name": "OrderInputIngressFilter", "boundary": "presentation", "responsibilities": ["Receive raw JSON payload", "Validate schema structural filter"]},
                {"name": "AuthenticationFilter", "boundary": "infrastructure", "responsibilities": ["Verify token signature", "Enforce authorization filter"]},
                {"name": "OrderEnrichmentProcessor", "boundary": "business_logic", "responsibilities": ["Enrich order with pricing", "Calculate sales tax processor"]},
                {"name": "PaymentChargingFilter", "boundary": "business_logic", "responsibilities": ["Execute payment charge filter", "Tokenize payment transaction"]},
                {"name": "DeliveryAssignmentProcessor", "boundary": "business_logic", "responsibilities": ["Assign driver filter stage", "Calculate ETA route processor"]},
                {"name": "NotificationDispatcherFilter", "boundary": "business_logic", "responsibilities": ["Dispatch customer push filter", "Format SMS receipt stage"]},
                {"name": "AuditLoggingFilter", "boundary": "infrastructure", "responsibilities": ["Append audit stream filter", "Log immutable transaction stage"]},
                {"name": "DatabaseSinkProcessor", "boundary": "data_access", "responsibilities": ["Write enriched record sink", "Persist final order state"]},
            ],
            "connectors": [
                {"from_component": "OrderInputIngressFilter", "to_component": "AuthenticationFilter", "connector_type": "data_flow"},
                {"from_component": "AuthenticationFilter", "to_component": "OrderEnrichmentProcessor", "connector_type": "data_flow"},
                {"from_component": "OrderEnrichmentProcessor", "to_component": "PaymentChargingFilter", "connector_type": "data_flow"},
                {"from_component": "PaymentChargingFilter", "to_component": "DeliveryAssignmentProcessor", "connector_type": "data_flow"},
                {"from_component": "DeliveryAssignmentProcessor", "to_component": "NotificationDispatcherFilter", "connector_type": "data_flow"},
                {"from_component": "NotificationDispatcherFilter", "to_component": "AuditLoggingFilter", "connector_type": "data_flow"},
                {"from_component": "AuditLoggingFilter", "to_component": "DatabaseSinkProcessor", "connector_type": "data_flow"},
            ]
        }
    }

    print("\n=======================================================")
    print("   RESEARCH EXPERIMENT: CROSS-STYLE BIAS VALIDATION   ")
    print("=======================================================\n")
    print("| Style | Detected Style | RTS | QAC | CI | CoS | SSM₁ (Name) | SSM₂ (Name) | CAS |")
    print("|-------|----------------|-----|-----|----|-----|-------------|-------------|-----|")

    results = {}
    for style_name, mock_arch in styles_mock.items():
        res = evaluate_architecture(mock_arch, requirements)
        results[style_name] = res

        ssm1_str = f"{res['SSM1']:.2f} ({res['ssm1_name']})"
        ssm2_str = f"{res['SSM2']:.2f} ({res['ssm2_name']})"
        print(
            f"| {style_name:13s} | {res['detected_style']:14s} | "
            f"{res['RTS']:.2f} | {res['QAC']:.2f} | {res['CI']:.2f} | {res['CoS']:.2f} | "
            f"{ssm1_str:11s} | {ssm2_str:11s} | {res['CAS']:.4f} |"
        )

    print("\n✅ Cross-style evaluation completed across all 5 styles.\n")
    return results


if __name__ == "__main__":
    run_cross_style_experiment()
