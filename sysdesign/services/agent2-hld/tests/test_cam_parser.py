import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from contracts.v1.architecture import Boundary, ElementType, ArchitecturePackage
from cam.parser import parse_cam, extract_json_from_text, CAMParseError


# ─── Hand-written CAM JSON Fixtures ──────────────────────────────────────────

LAYERED_FIXTURE = """
{
  "architecture_style": "Layered Architecture",
  "style_confidence": 0.95,
  "layers": [
    {"name": "Presentation", "order": 1},
    {"name": "Business Logic", "order": 2},
    {"name": "Data Access", "order": 3}
  ],
  "components": [
    {
      "name": "OrderController",
      "layer": "Presentation",
      "element_type": "controller",
      "responsibility": "Handles HTTP order checkout requests and input validation",
      "provided_interfaces": ["POST /orders"],
      "required_interfaces": ["OrderService"],
      "requirement_ids": ["FR-1"]
    },
    {
      "name": "OrderService",
      "layer": "Business Logic",
      "element_type": "service",
      "responsibility": "Processes business rules for order fulfillment and discounts",
      "provided_interfaces": ["OrderService"],
      "required_interfaces": ["OrderRepository"],
      "requirement_ids": ["FR-1", "FR-2"]
    },
    {
      "name": "OrderRepository",
      "layer": "Data Access",
      "element_type": "repository",
      "responsibility": "Persists order entities to PostgreSQL database",
      "provided_interfaces": ["OrderRepository"],
      "required_interfaces": ["Database"],
      "requirement_ids": ["FR-2"]
    }
  ],
  "interactions": [
    {
      "from": "OrderController",
      "to": "OrderService",
      "type": "sync_call",
      "protocol": "REST"
    },
    {
      "from": "OrderService",
      "to": "OrderRepository",
      "type": "sync_call",
      "protocol": "SQL"
    }
  ]
}
"""

MICROSERVICES_FENCED_FIXTURE = """
Here is the recommended microservices architecture for your project:

```json
{
  "architecture_style": "Microservices Architecture",
  "style_confidence": 0.88,
  "components": [
    {
      "name": "ApiGateway",
      "boundary": "presentation",
      "element_type": "gateway",
      "responsibility": "Routes incoming requests to downstream microservices and enforces authentication",
      "requirement_ids": ["FR-1", "NFR-2"]
    },
    {
      "name": "UserService",
      "boundary": "business_logic",
      "element_type": "service",
      "responsibility": "Manages user profiles and authentication tokens",
      "requirement_ids": ["FR-2"]
    },
    {
      "name": "PaymentService",
      "boundary": "business_logic",
      "element_type": "service",
      "responsibility": "Handles credit card payment processing with PCI compliance",
      "requirement_ids": ["FR-3", "NFR-1"]
    }
  ],
  "connectors": [
    {
      "from": "ApiGateway",
      "to": "UserService",
      "type": "sync_call",
      "protocol": "gRPC"
    },
    {
      "from": "ApiGateway",
      "to": "PaymentService",
      "type": "sync_call",
      "protocol": "gRPC"
    }
  ]
}
```

This architecture ensures independent scalability.
"""

EVENT_DRIVEN_FIXTURE = """
{
  "architecture_style": "Event-Driven Architecture",
  "components": [
    {
      "name": "TelemetryProducer",
      "boundary": "presentation",
      "element_type": "client",
      "responsibility": "Publishes real-time sensor events to message broker"
    },
    {
      "name": "EventBroker",
      "boundary": "infrastructure",
      "element_type": "broker",
      "responsibility": "Central Kafka cluster managing event topics and subscriptions"
    },
    {
      "name": "AnalyticsConsumer",
      "boundary": "business_logic",
      "element_type": "handler",
      "responsibility": "Consumes stream events and computes windowed metrics"
    }
  ],
  "interactions": [
    {
      "from": "TelemetryProducer",
      "to": "EventBroker",
      "type": "event_publish",
      "protocol": "AMQP"
    },
    {
      "from": "EventBroker",
      "to": "AnalyticsConsumer",
      "type": "async_message",
      "protocol": "Kafka"
    }
  ]
}
"""

LOOSE_JSON_WITH_COMMENTS = """
{
  "architecture_style": "Layered Architecture",
  "components": [
    {
      "name": "AuthService",
      "layer": "Business",
      "responsibility": "Manages user login and JWT token validation", // trailing comment
    },
    {
      "name": "UserRepo",
      "layer": "Data Access",
      "responsibility": "Queries user records from database",
    },
  ], // trailing comma
  "interactions": [
    {
      "from": "AuthService",
      "to": "UserRepo",
      "type": "sync_call",
    },
  ],
}
"""


# ─── Tests ───────────────────────────────────────────────────────────────────

def test_parse_layered_architecture_json():
    cam = parse_cam(LAYERED_FIXTURE, job_id="job-101", project_name="Order System")

    assert isinstance(cam, ArchitecturePackage)
    assert cam.architecture_style == "Layered Architecture"
    assert cam.job_id == "job-101"
    assert len(cam.components) == 3
    assert len(cam.connectors) == 2

    # Check boundaries and element types
    controller = next(c for c in cam.components if c.name == "OrderController")
    assert controller.boundary == Boundary.PRESENTATION
    assert controller.element_type == ElementType.CONTROLLER
    assert "POST /orders" in controller.provided_interfaces

    repo = next(c for c in cam.components if c.name == "OrderRepository")
    assert repo.boundary == Boundary.DATA
    assert repo.element_type == ElementType.REPOSITORY


def test_parse_microservices_architecture_fenced():
    cam = parse_cam(MICROSERVICES_FENCED_FIXTURE, job_id="job-202", project_name="E-Commerce")

    assert isinstance(cam, ArchitecturePackage)
    assert cam.architecture_style == "Microservices Architecture"
    assert len(cam.components) == 3

    gateway = next(c for c in cam.components if c.name == "ApiGateway")
    assert gateway.element_type == ElementType.GATEWAY
    assert gateway.boundary == Boundary.PRESENTATION


def test_parse_event_driven_architecture():
    cam = parse_cam(EVENT_DRIVEN_FIXTURE, job_id="job-303", project_name="IoT Stream")

    assert cam.architecture_style == "Event-Driven Architecture"
    broker = next(c for c in cam.components if c.name == "EventBroker")
    assert broker.element_type == ElementType.BROKER
    assert broker.boundary == Boundary.INFRASTRUCTURE

    assert len(cam.connectors) == 2
    assert cam.connectors[0].connector_type == "event_publish"
    assert cam.connectors[1].connector_type == "async_message"


def test_parse_json_with_comments_and_loose_formatting():
    cam = parse_cam(LOOSE_JSON_WITH_COMMENTS, job_id="job-404")

    assert cam.architecture_style == "Layered Architecture"
    assert len(cam.components) == 2
    assert len(cam.connectors) == 1


def test_parse_invalid_json_raises_cam_parse_error():
    invalid_text = "This is just plain text without any JSON content."

    with pytest.raises(CAMParseError):
        parse_cam(invalid_text)
