"""
Comprehensive Unit & Integration Test Suite for Agent 3 (LLD)
Validating:
- Class Diagram method signatures, multiplicities, dependency direction, undefined endpoint detection, composition ownership
- Sequence Diagram participant roles, arrows, activation lifecycle, nesting (alt/else/end, loop, opt), causal ordering
- ER Diagram primary keys, attributes, semantic relationships, cardinality preservation, architectural entity filtering
- Backward compatibility with legacy payloads and safe handling of failed HLD input
"""
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("GROQ_API_KEY", "test-key")

import pytest
from schemas.ir_schema import (
    IntermediateRepresentation,
    ClassIR,
    ClassRelationship,
    Method,
    MethodParameter,
    Visibility,
    EntityIR,
    EntityAttribute,
    EntityRelationship,
    SequenceIR,
    SequenceMessage,
    MessageType,
    ParticipantType,
)
from utils.irMapper import convert_to_ir, _parse_method_object
from utils.irGenerator import (
    generate_class_plantuml,
    generate_sequence_plantuml,
    generate_er_plantuml,
    is_invalid_relationship_name,
)
from utils.plantUmlGenerator import generate_plantuml
from validators.stage_validators import validate_er_diagram, validate_class_diagram
from validators.consistency_engine import ConsistencyEngine
from Controllers.umlController import _build_requirements_text
from schemas.umlSchema import GenerateRequest, HighLevelArchitecture, ArchitecturalLayer, FunctionalRequirement


# ============================================================================
# 1. CLASS DIAGRAM TESTS
# ============================================================================

def test_class_method_signature_parsing_and_plantuml_rendering():
    """Method signatures preserve parameters, parameter types, return types, and visibility."""
    # Test method parser directly
    m1 = _parse_method_object("setStatus(status: string): void")
    assert m1.name == "setStatus"
    assert len(m1.parameters) == 1
    assert m1.parameters[0].name == "status"
    assert m1.parameters[0].data_type == "string"
    assert m1.return_type == "void"
    assert m1.visibility == Visibility.PUBLIC

    m2 = _parse_method_object("-calculateTotal(items: List<Item>, taxRate: float): float")
    assert m2.name == "calculateTotal"
    assert len(m2.parameters) == 2
    assert m2.parameters[0].name == "items"
    assert m2.parameters[0].data_type == "List<Item>"
    assert m2.parameters[1].name == "taxRate"
    assert m2.parameters[1].data_type == "float"
    assert m2.return_type == "float"
    assert m2.visibility == Visibility.PRIVATE

    # Test rendering in PlantUML
    class_diagram = {
        "classes": [
            {
                "name": "OrderService",
                "attributes": ["orderId: string"],
                "methods": [
                    "setStatus(status: string): void",
                    "-calculateTotal(items: List<Item>, taxRate: float): float",
                    "getOrder(): Order",
                    "+legacyMethod()",
                ],
            }
        ],
        "relationships": [],
    }

    plantuml = generate_class_plantuml(class_diagram)
    assert "+setStatus(status: string): void" in plantuml
    assert "-calculateTotal(items: List<Item>, taxRate: float): float" in plantuml
    assert "+getOrder(): Order" in plantuml
    assert "+legacyMethod()" in plantuml


def test_class_cardinality_preservation_and_no_silent_invention():
    """Cardinality 1..* stays 1..* (never converted to *), and source multiplicity is not invented."""
    class_diagram = {
        "classes": [
            {"name": "Session", "attributes": ["sessionId"], "methods": []},
            {"name": "Requirement", "attributes": ["reqId"], "methods": []},
            {"name": "User", "attributes": ["userId"], "methods": []},
            {"name": "Profile", "attributes": ["profileId"], "methods": []},
        ],
        "relationships": [
            # 1..* must stay 1..*, source not invented
            {
                "source": "Session",
                "target": "Requirement",
                "type": "association",
                "cardinality": "1..*",
            },
            # Explicit source and target multiplicities
            {
                "source": "User",
                "target": "Profile",
                "type": "association",
                "source_multiplicity": "1",
                "target_multiplicity": "0..1",
            },
        ],
    }

    plantuml = generate_class_plantuml(class_diagram)
    # Must preserve 1..* and NOT convert to generic *
    assert 'Session -- "1..*" Requirement' in plantuml
    assert 'Session "1" -- "*"' not in plantuml
    # Must preserve explicit multiplicities
    assert 'User "1" -- "0..1" Profile' in plantuml


def test_class_dependency_direction_and_no_multiplicity():
    """Dependencies must point Source ..> Target and must NOT attach structural multiplicities."""
    class_diagram = {
        "classes": [
            {"name": "OrderController", "attributes": [], "methods": []},
            {"name": "OrderService", "attributes": [], "methods": []},
        ],
        "relationships": [
            {
                "source": "OrderController",
                "target": "OrderService",
                "type": "dependency",
                "cardinality": "1",  # Should be ignored on dependency
            }
        ],
    }

    # Test both active and backup renderers
    plantuml1 = generate_class_plantuml(class_diagram)
    assert "OrderController ..> OrderService" in plantuml1
    assert 'OrderController "1" ..> "1" OrderService' not in plantuml1

    plantuml2 = generate_plantuml(class_diagram)
    assert "OrderController ..> OrderService" in plantuml2
    assert "<.." not in plantuml2  # Must not reverse arrow


def test_class_composition_and_aggregation_ownership():
    """Whole-part diamond must appear at the appropriate whole/owner endpoint."""
    class_diagram = {
        "classes": [
            {"name": "Car", "attributes": [], "methods": []},
            {"name": "Engine", "attributes": [], "methods": []},
            {"name": "Department", "attributes": [], "methods": []},
            {"name": "Employee", "attributes": [], "methods": []},
        ],
        "relationships": [
            # Default: source is owner
            {"source": "Car", "target": "Engine", "type": "composition"},
            # Explicit: target is owner
            {"source": "Employee", "target": "Department", "type": "aggregation", "ownership": "target"},
        ],
    }

    plantuml = generate_class_plantuml(class_diagram)
    assert "Car *-- Engine" in plantuml
    assert "Employee --o Department" in plantuml


def test_class_undefined_relationship_endpoints_detected():
    """Undefined relationship endpoints must be logged/detected and not silently create dummy classes."""
    parsed_json = {
        "class_diagram": {
            "classes": [
                {"name": "ExistingClass", "attributes": ["id"], "methods": []}
            ],
            "relationships": [
                {
                    "source": "NonExistentClass",
                    "target": "ExistingClass",
                    "type": "association",
                }
            ],
        }
    }

    ir = convert_to_ir(parsed_json)
    # Undefined source should not be added to ir.classes
    assert len(ir.classes) == 1
    assert ir.classes[0].name == "ExistingClass"


# ============================================================================
# 2. SEQUENCE DIAGRAM TESTS
# ============================================================================

def test_sequence_activation_deactivation_lifecycle():
    """Return message must deactivate the sender whose execution is ending, NEVER the receiver."""
    sequence = {
        "name": "Activation Lifecycle Test",
        "participants": ["Frontend", "OrderService"],
        "participant_types": {
            "Frontend": "boundary",
            "OrderService": "service",
        },
        "messages": [
            {"from": "Frontend", "to": "OrderService", "message": "doWork()", "type": "call", "activate": True},
            {"from": "OrderService", "to": "Frontend", "message": "result", "type": "return", "deactivate": True},
        ],
    }

    plantuml = generate_sequence_plantuml(sequence)

    assert "Frontend -> OrderService: doWork()" in plantuml
    assert "activate OrderService" in plantuml
    assert "OrderService --> Frontend: result" in plantuml
    assert "deactivate OrderService" in plantuml
    # Must NOT deactivate response receiver
    assert "deactivate Frontend" not in plantuml


def test_sequence_nested_calls_and_self_calls():
    """Nested method calls and self-calls must maintain accurate activation lifelines."""
    sequence = {
        "name": "Nested Calls Test",
        "participants": ["Client", "ServiceA", "ServiceB"],
        "participant_types": {
            "Client": "actor",
            "ServiceA": "service",
            "ServiceB": "service",
        },
        "messages": [
            {"from": "Client", "to": "ServiceA", "message": "request()", "type": "call", "activate": True},
            {"from": "ServiceA", "to": "ServiceA", "message": "validate()", "type": "call", "activate": True, "deactivate": True},
            {"from": "ServiceA", "to": "ServiceB", "message": "query()", "type": "call", "activate": True},
            {"from": "ServiceB", "to": "ServiceA", "message": "data", "type": "return", "deactivate": True},
            {"from": "ServiceA", "to": "Client", "message": "response", "type": "return", "deactivate": True},
        ],
    }

    plantuml = generate_sequence_plantuml(sequence)
    assert "activate ServiceA" in plantuml
    assert "activate ServiceB" in plantuml
    assert "deactivate ServiceB" in plantuml
    assert "deactivate ServiceA" in plantuml
    assert "deactivate Client" not in plantuml


def test_sequence_alt_else_end_nesting():
    """alt fragments containing else branches must ALWAYS properly close with end."""
    sequence = {
        "name": "Alt Else Test",
        "participants": ["User", "AuthService"],
        "items": [
            {
                "type": "alt",
                "condition": "valid credentials",
                "messages": [
                    {"from": "User", "to": "AuthService", "message": "login()", "type": "call"},
                    {"from": "AuthService", "to": "User", "message": "token", "type": "return"},
                ],
                "logic_blocks": [
                    {
                        "type": "else",
                        "condition": "invalid credentials",
                        "messages": [
                            {"from": "AuthService", "to": "User", "message": "error401", "type": "return"}
                        ],
                    }
                ],
            }
        ],
    }

    plantuml = generate_sequence_plantuml(sequence)
    assert "alt [valid credentials]" in plantuml
    assert "else [invalid credentials]" in plantuml
    assert "end" in plantuml
    # Verify proper ordering: alt -> else -> end
    pos_alt = plantuml.find("alt [valid credentials]")
    pos_else = plantuml.find("else [invalid credentials]")
    pos_end = plantuml.find("end")
    assert pos_alt < pos_else < pos_end


def test_sequence_causal_ordering_and_no_ortho():
    """Sequence diagram must preserve causal order and omit skinparam linetype ortho."""
    sequence = {
        "name": "Interleaved Causal Ordering",
        "participants": ["A", "B"],
        "items": [
            {"from": "A", "to": "B", "message": "step1()", "type": "call"},
            {
                "type": "loop",
                "condition": "count < 3",
                "messages": [
                    {"from": "A", "to": "B", "message": "step2_loop()", "type": "call"}
                ],
            },
            {"from": "B", "to": "A", "message": "step3()", "type": "return"},
        ],
    }

    plantuml = generate_sequence_plantuml(sequence)
    assert "hide footbox" in plantuml
    assert "skinparam linetype ortho" not in plantuml

    pos1 = plantuml.find("step1()")
    pos2 = plantuml.find("step2_loop()")
    pos3 = plantuml.find("step3()")
    assert pos1 < pos2 < pos3


# ============================================================================
# 3. ER DIAGRAM TESTS
# ============================================================================

def test_er_cardinality_preservation():
    """ER multiplicities 1..* must be preserved as (1,N), 0..* as (0,N), never generic N."""
    er_diagram = {
        "entities": [
            {"name": "Department", "attributes": ["dept_id"], "primary_key": "dept_id"},
            {"name": "Employee", "attributes": ["emp_id"], "primary_key": "emp_id"},
        ],
        "relationships": [
            {
                "name": "EMPLOYS",
                "source": "Department",
                "target": "Employee",
                "source_multiplicity": "1",
                "target_multiplicity": "1..*",
            }
        ],
    }

    plantuml = generate_er_plantuml(er_diagram)
    assert 'relationship "EMPLOYS" as REL_0' in plantuml
    assert "REL_0-1- DEPARTMENT" in plantuml
    assert "REL_0-(1,N)- EMPLOYEE" in plantuml


def test_er_excludes_architectural_components():
    """Architectural components (services, controllers, repos) must NOT be ER entities."""
    er_diagram = {
        "entities": [
            {"name": "Order", "attributes": ["order_id"], "primary_key": "order_id"},
            {"name": "OrderService", "attributes": ["service_id"], "primary_key": "service_id"},
            {"name": "OrderController", "attributes": ["ctrl_id"], "primary_key": "ctrl_id"},
            {"name": "OrderRepository", "attributes": ["repo_id"], "primary_key": "repo_id"},
        ],
        "relationships": [
            {"name": "CONTAINS", "source": "Order", "target": "OrderService", "type": "one-to-many"}
        ],
    }

    # Generator must filter out architectural components
    plantuml = generate_er_plantuml(er_diagram)
    assert 'entity "Order" as ORDER' in plantuml
    assert "ORDERSERVICE" not in plantuml
    assert "ORDERCONTROLLER" not in plantuml
    assert "ORDERREPOSITORY" not in plantuml

    # Validator must reject architectural components in ER
    report = validate_er_diagram(er_diagram, class_diagram={})
    assert not report["passed"]
    error_codes = [e["code"] for e in report["errors"]]
    assert "ARCHITECTURAL_COMPONENT_AS_ENTITY" in error_codes


def test_er_consistency_engine_cv009():
    """ConsistencyEngine flags architectural components in ER entities under CV-009."""
    ir = IntermediateRepresentation(
        classes=[ClassIR(name="Order")],
        entities=[
            EntityIR(name="Order", attributes=[EntityAttribute(name="id", constraint="PK")]),
            EntityIR(name="PaymentService", attributes=[EntityAttribute(name="id", constraint="PK")]),
        ],
    )
    engine = ConsistencyEngine()
    report = engine.validate(ir)
    rule_ids = [e.rule_id for e in report.errors]
    assert "CV-009" in rule_ids


# ============================================================================
# 4. BACKWARD COMPATIBILITY & FAILED HLD HANDLING
# ============================================================================

def test_failed_hld_handled_safely():
    """Failed HLD input must not be treated as a valid architecture pattern or crash generation."""
    req = GenerateRequest(
        project_name="E-Commerce",
        project_description="Online shopping system",
        high_level_architecture=HighLevelArchitecture(
            pattern="Failed",
            layers=[ArchitecturalLayer(name="None specified")],
            architectural_constraints=["None specified"],
        ),
        functional_requirements=[
            FunctionalRequirement(id="FR-1", title="Browse Products", description="Users can view products")
        ],
    )

    requirements_text, req_ids = _build_requirements_text(req)
    assert "Architecture Pattern: Failed" not in requirements_text
    assert "Provisional" in requirements_text
    assert "None specified" not in requirements_text
    assert "FR-1" in req_ids


def test_backward_compatibility_legacy_payload():
    """Legacy JSON payloads with old field names and string methods still parse and render."""
    legacy_json = {
        "class_diagram": {
            "classes": [
                {
                    "name": "Invoice",
                    "attributes": ["invoice_id"],
                    "methods": ["calculateTax()"],
                }
            ],
            "relationships": [
                {
                    "source": "Invoice",
                    "target": "LineItem",
                    "type": "association",
                    "cardinality": "1..*",
                }
            ],
        },
        "sequence_diagrams": [
            {
                "name": "Generate Invoice",
                "participants": ["BillingController", "Invoice"],
                "messages": [
                    {"from": "BillingController", "to": "Invoice", "message": "calculateTax()"}
                ],
            }
        ],
        "er_diagram": {
            "entities": [
                {"name": "Invoice", "attributes": ["invoice_id", "total"], "primary_key": "invoice_id"}
            ],
            "relationships": [],
        },
    }

    ir = convert_to_ir(legacy_json)
    assert len(ir.classes) == 1
    assert ir.classes[0].methods[0].name == "calculateTax"
    assert ir.classes[0].methods[0].return_type == "void"

    class_uml = generate_class_plantuml(legacy_json["class_diagram"])
    assert "+calculateTax()" in class_uml
    assert 'Invoice -- "1..*" LineItem' in class_uml

    # Also test rendering with IR dataclass directly
    from schemas.ir_schema import MethodParameter
    ir_class_diagram = {
        "classes": [
            {
                "name": "Invoice",
                "attributes": ["invoice_id"],
                "methods": ir.classes[0].methods,
            }
        ],
        "relationships": [],
    }
    ir_class_uml = generate_class_plantuml(ir_class_diagram)
    assert "+calculateTax(): void" in ir_class_uml

    seq_uml = generate_sequence_plantuml(legacy_json["sequence_diagrams"][0])
    assert "BillingController -> Invoice: calculateTax()" in seq_uml

    er_uml = generate_er_plantuml(legacy_json["er_diagram"])
    assert 'entity "Invoice" as INVOICE' in er_uml
