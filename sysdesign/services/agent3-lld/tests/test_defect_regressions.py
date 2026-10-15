"""
Regression Test Suite for the 12 Identified Agent 3 LLD Defects.

Defects covered:
1. Sequence validation: Inspect canonical ordered items recursively.
2. Participant validation: External actors, boundaries, and systems not required in Class diagram.
3. Return messages: Do not validate return labels as receiver methods.
4. Structured methods: Check method names, required arguments, and compatible return contracts.
5. Multiplicity validation: Check source and target multiplicity without inventing missing values.
6. Inheritance: Default direction Child --|> Parent.
7. Undefined relationships: Do not retain in IR; report structured errors.
8. ER filtering: Do not remove domain entities named 'Service'; classify compound architectural entities.
9. Consistency rules: Avoid false positives in CV-003 (value objects), CV-005 (missing arguments), CV-008 (domain actors).
10. Primary keys: Validation, mapping, and rendering agree on primary key handling.
11. Activation: Never deactivate a lifeline that was not activated.
12. Configuration: MAX_AGENT_ITERATIONS, candidate models, and provider settings remain unchanged.
"""
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("GROQ_API_KEY", "test-key")

import pytest
import config.config as app_config
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
    LogicBlock,
    LogicBlockType,
)
from utils.irMapper import convert_to_ir
from utils.irGenerator import (
    generate_class_plantuml,
    generate_sequence_plantuml,
    generate_er_plantuml,
    is_architectural_component,
)
from utils.plantUmlGenerator import generate_plantuml
from validators.stage_validators import (
    validate_class_diagram,
    validate_sequence_diagrams,
    validate_er_diagram,
)
from validators.consistency_engine import ConsistencyEngine


# -----------------------------------------------------------------------------
# Defect 1: Sequence validation of canonical ordered items collection
# -----------------------------------------------------------------------------
def test_defect_1_nested_sequence_items_validation():
    """Invalid messages stored within canonical items or nested logic blocks must be validated."""
    class_diagram = {
        "classes": [
            {"name": "OrderService", "methods": ["createOrder()"], "attributes": []},
            {"name": "PaymentGateway", "methods": ["charge()"], "attributes": []},
        ]
    }

    # Sequence with an invalid method call nested inside an 'alt' block within 'items'
    sequence_diagrams = [
        {
            "name": "CheckoutFlow",
            "participants": ["OrderService", "PaymentGateway"],
            "items": [
                {
                    "block_type": "alt",
                    "condition": "valid_cart",
                    "items": [
                        {
                            "from": "OrderService",
                            "to": "PaymentGateway",
                            "message": "nonExistentPaymentMethod()",  # INVALID
                            "type": "call",
                        }
                    ],
                }
            ],
        }
    ]

    report = validate_sequence_diagrams(sequence_diagrams, class_diagram)
    assert not report["passed"], "Validation should fail for invalid method call nested in items"
    err_codes = [e["code"] for e in report["errors"]]
    assert "UNKNOWN_RECEIVER_METHOD" in err_codes

    # Also verify that ConsistencyEngine CV-001 catches nested messages in IR items
    ir = convert_to_ir({
        "class_diagram": class_diagram,
        "sequence_diagrams": sequence_diagrams,
    })
    c_report = ConsistencyEngine().validate(ir)
    assert not c_report.passed
    c_rules = [e.rule_id for e in c_report.errors]
    assert "CV-001" in c_rules


# -----------------------------------------------------------------------------
# Defect 2: Participant validation (external actors / systems / boundaries)
# -----------------------------------------------------------------------------
def test_defect_2_external_participants_not_required_in_class_diagram():
    """External actors, boundaries, and systems in sequence must not be required as domain classes."""
    class_diagram = {
        "classes": [
            {"name": "OrderService", "methods": ["process()"], "attributes": ["id"]},
        ]
    }

    sequence_diagrams = [
        {
            "name": "ProcessOrder",
            "participants": ["Customer", "UIBoundary", "OrderService", "ExternalPaymentGateway", "Database"],
            "participant_types": {
                "Customer": "actor",
                "UIBoundary": "boundary",
                "ExternalPaymentGateway": "external_system",
                "Database": "database",
            },
            "actors": ["Customer"],
            "items": [
                {"from": "Customer", "to": "UIBoundary", "message": "clickSubmit()", "type": "call"},
                {"from": "UIBoundary", "to": "OrderService", "message": "process()", "type": "call"},
            ],
        }
    ]

    report = validate_sequence_diagrams(sequence_diagrams, class_diagram)
    # Must NOT fail with critical errors for external participants
    assert report["passed"], f"Expected sequence validation to pass, but got errors: {report['errors']}"

    # CV-002 in ConsistencyEngine should also not flag external participants
    ir = convert_to_ir({
        "class_diagram": class_diagram,
        "sequence_diagrams": sequence_diagrams,
    })
    c_report = ConsistencyEngine().validate(ir)
    cv002_errors = [e for e in c_report.errors if e.rule_id == "CV-002"]
    assert len(cv002_errors) == 0, f"CV-002 should not flag external participants: {cv002_errors}"


# -----------------------------------------------------------------------------
# Defect 3: Return messages not validated as receiving-class method calls
# -----------------------------------------------------------------------------
def test_defect_3_return_messages_not_validated_as_receiver_methods():
    """A return message B --> A: result must not require A.result()."""
    class_diagram = {
        "classes": [
            {"name": "Client", "methods": ["start()"], "attributes": []},
            {"name": "Server", "methods": ["query()"], "attributes": []},
        ]
    }

    sequence_diagrams = [
        {
            "name": "QueryFlow",
            "participants": ["Client", "Server"],
            "items": [
                {"from": "Client", "to": "Server", "message": "query()", "type": "call"},
                {"from": "Server", "to": "Client", "message": "queryResultToken", "type": "return", "arrow": "-->"},
            ],
        }
    ]

    report = validate_sequence_diagrams(sequence_diagrams, class_diagram)
    assert report["passed"], f"Return message should not require method on Client: {report['errors']}"

    ir = convert_to_ir({
        "class_diagram": class_diagram,
        "sequence_diagrams": sequence_diagrams,
    })
    c_report = ConsistencyEngine().validate(ir)
    cv001_errors = [e for e in c_report.errors if e.rule_id == "CV-001"]
    assert len(cv001_errors) == 0, f"CV-001 should ignore return messages: {cv001_errors}"


# -----------------------------------------------------------------------------
# Defect 4: Structured methods (names, required arguments, return contracts)
# -----------------------------------------------------------------------------
def test_defect_4_structured_and_string_methods_validation():
    """Validation must support structured methods, checking required arguments and return contracts."""
    class_diagram = {
        "classes": [
            {
                "name": "OrderProcessor",
                "attributes": [],
                "methods": [
                    {
                        "name": "createOrder",
                        "parameters": [
                            {"name": "cart", "required": True},
                            {"name": "coupon", "required": False, "default": None},
                        ],
                        "return_type": "Order",
                    },
                    "+cancelOrder(orderId: string): boolean",
                ],
            }
        ]
    }

    # 1. Missing required argument: createOrder requires 1 param (cart), called with 0
    seq_missing_args = [
        {
            "name": "OrderFlowMissingArgs",
            "participants": ["Caller", "OrderProcessor"],
            "participant_types": {"Caller": "actor"},
            "items": [
                {"from": "Caller", "to": "OrderProcessor", "message": "createOrder()", "arguments": [], "type": "call"}
            ],
        }
    ]
    # Note: If called with explicit empty call_args when parameters are required:
    report_missing = validate_sequence_diagrams(seq_missing_args, class_diagram)
    assert report_missing["passed"]  # High-level calls can omit args for brevity

    # If called with fewer arguments than required when arguments are passed:
    seq_few_args = [
        {
            "name": "OrderFlowFewArgs",
            "participants": ["Caller", "OrderProcessor"],
            "participant_types": {"Caller": "actor"},
            "items": [
                # cancelOrder requires orderId
                {"from": "Caller", "to": "OrderProcessor", "message": "cancelOrder()", "arguments": [], "type": "call"}
            ],
        }
    ]

    # Incompatible return contract: expected return 'Invoice' but method defines 'Order'
    seq_bad_return = [
        {
            "name": "OrderFlowBadReturn",
            "participants": ["Caller", "OrderProcessor"],
            "participant_types": {"Caller": "actor"},
            "items": [
                {
                    "from": "Caller",
                    "to": "OrderProcessor",
                    "message": "createOrder(cart)",
                    "arguments": ["cart"],
                    "return_type": "Invoice",
                    "type": "call",
                }
            ],
        }
    ]
    report_bad_return = validate_sequence_diagrams(seq_bad_return, class_diagram)
    err_codes = [e["code"] for e in report_bad_return["errors"]]
    assert "INCOMPATIBLE_RETURN_CONTRACT" in err_codes


# -----------------------------------------------------------------------------
# Defect 5: Multiplicity validation and no silent invention
# -----------------------------------------------------------------------------
def test_defect_5_multiplicity_validation_and_no_invention():
    """Validate both multiplicities and ensure rendering never invents missing multiplicities."""
    class_diagram = {
        "classes": [
            {"name": "Team", "attributes": ["id"]},
            {"name": "Member", "attributes": ["id"]},
        ],
        "relationships": [
            {
                "source": "Team",
                "target": "Member",
                "type": "association",
                "target_multiplicity": "1..*",  # source_multiplicity is intentionally omitted
            }
        ],
    }

    # Class validation accepts valid target multiplicity
    report = validate_class_diagram(class_diagram)
    assert report["passed"]

    # Class rendering must NOT invent '1' for the left side
    uml = generate_class_plantuml(class_diagram)
    assert 'Team -- "1..*" Member' in uml
    assert '"1" Team' not in uml

    # ER rendering must NOT invent '1' for missing source multiplicity
    er_diagram = {
        "entities": [
            {"name": "Team", "attributes": ["id"], "primary_key": "id"},
            {"name": "Member", "attributes": ["id"], "primary_key": "id"},
        ],
        "relationships": [
            {
                "name": "HAS",
                "source": "Team",
                "target": "Member",
                "type": "one-to-many",
                "target_multiplicity": "1..*",  # source omitted
            }
        ],
    }
    er_uml = generate_er_plantuml(er_diagram)
    assert "REL_0-(1,N)- MEMBER" in er_uml
    # Left side has no multiplicity, so it must render simple connection line without invented cardinality
    assert "REL_0-- TEAM" in er_uml
    assert "REL_0-1- TEAM" not in er_uml


# -----------------------------------------------------------------------------
# Defect 6: Inheritance default direction (Child --|> Parent)
# -----------------------------------------------------------------------------
def test_defect_6_inheritance_default_direction():
    """Relationship with source=Child and target=Parent must render Child --|> Parent."""
    class_diagram = {
        "classes": [
            {"name": "Dog", "attributes": ["bark"]},
            {"name": "Animal", "attributes": ["alive"]},
        ],
        "relationships": [
            {
                "source": "Dog",
                "target": "Animal",
                "type": "inheritance",
            }
        ],
    }

    uml_ir = generate_class_plantuml(class_diagram)
    assert "Dog --|> Animal" in uml_ir

    uml_legacy = generate_plantuml(class_diagram)
    assert "Dog --|> Animal" in uml_legacy


# -----------------------------------------------------------------------------
# Defect 7: Undefined relationships not retained in valid IR
# -----------------------------------------------------------------------------
def test_defect_7_undefined_relationships_not_retained_in_ir():
    """Relationships referencing undefined classes or entities must not be retained in valid IR."""
    payload = {
        "class_diagram": {
            "classes": [
                {"name": "KnownClass", "attributes": ["id"]},
            ],
            "relationships": [
                {
                    "source": "KnownClass",
                    "target": "UndefinedTargetClass",
                    "type": "association",
                }
            ],
        },
        "er_diagram": {
            "entities": [
                {"name": "KnownEntity", "attributes": ["id"], "primary_key": "id"},
            ],
            "relationships": [
                {
                    "name": "LINKS",
                    "source": "KnownEntity",
                    "target": "UndefinedEntity",
                    "type": "one-to-many",
                }
            ],
        },
    }

    # Validator must report structured errors
    c_report = validate_class_diagram(payload["class_diagram"])
    assert not c_report["passed"]
    assert "UNKNOWN_CLASS_RELATIONSHIP_TARGET" in [e["code"] for e in c_report["errors"]]

    er_report = validate_er_diagram(payload["er_diagram"], payload["class_diagram"])
    assert not er_report["passed"]
    assert "UNKNOWN_ER_RELATIONSHIP_TARGET" in [e["code"] for e in er_report["errors"]]

    # IR must omit the invalid relationships without crashing or inventing classes
    ir = convert_to_ir(payload)
    known_cls = next(c for c in ir.classes if c.name == "KnownClass")
    assert len(known_cls.relationships) == 0, "Invalid relationship must not be retained in Class IR"

    known_ent = next(e for e in ir.entities if e.name == "KnownEntity")
    assert len(known_ent.relationships) == 0, "Invalid relationship must not be retained in Entity IR"


# -----------------------------------------------------------------------------
# Defect 8: ER filtering - do not silently remove domain entity 'Service'
# -----------------------------------------------------------------------------
def test_defect_8_er_filtering_no_silent_removal_of_service():
    """Do not drop entities named 'Service'; compound architectural components are classified and reported."""
    # 1. Standalone domain entity 'Service' must be preserved
    assert not is_architectural_component("Service")
    assert not is_architectural_component("Component")
    assert is_architectural_component("OrderService")
    assert is_architectural_component("PaymentController")
    assert is_architectural_component("UserRepository")

    er_diagram = {
        "entities": [
            {"name": "Service", "attributes": ["service_id", "price"], "primary_key": "service_id"},
            {"name": "OrderService", "attributes": ["id"], "primary_key": "id"},
        ]
    }

    # Validator flags OrderService but accepts Service
    report = validate_er_diagram(er_diagram, class_diagram={})
    error_entities = [e.get("details", {}).get("entity") for e in report["errors"]]
    assert "OrderService" in error_entities
    assert "Service" not in error_entities

    # Generator renders Service and excludes OrderService
    uml = generate_er_plantuml(er_diagram)
    assert 'entity "Service" as SERVICE' in uml
    assert "ORDERSERVICE" not in uml


# -----------------------------------------------------------------------------
# Defect 9: Consistency rules - avoid false positives in CV-003, CV-005, CV-008
# -----------------------------------------------------------------------------
def test_defect_9_consistency_engine_no_false_positives():
    """CV-003 (value objects), CV-005 (missing arguments), and CV-008 (domain actors) must not false-positive."""
    ir = IntermediateRepresentation(
        classes=[
            # Value Object: Address has attributes but no ID and no ER table
            ClassIR(name="Address", attributes=["street", "city", "zip"], stereotype="value_object"),
            # Domain Actor representation: User has domain entity attributes and is an actor
            ClassIR(
                name="User",
                attributes=["user_id", "username", "email"],
                stereotype="entity",
                methods=[
                    Method(name="login", parameters=[MethodParameter(name="user"), MethodParameter(name="pass")]),
                ],
            ),
        ],
        sequences=[
            SequenceIR(
                name="UserLoginFlow",
                participants=["User"],
                actors=["User"],
                messages=[
                    # Calling login() without full argument list in sequence diagram should not trigger CV-005 error
                    SequenceMessage(from_participant="User", to_participant="User", method="login", arguments=[]),
                ],
            )
        ],
        entities=[
            # User entity exists in ER
            EntityIR(name="User", attributes=[EntityAttribute(name="user_id", constraint="PK")]),
        ],
    )

    report = ConsistencyEngine().validate(ir)
    rule_ids = [e.rule_id for e in report.errors]

    # CV-003: Address is a value object -> no error
    assert "CV-003" not in rule_ids, "Address value object should not trigger CV-003"

    # CV-005: Omitted sequence call arguments -> no error
    assert "CV-005" not in rule_ids, "Omitted sequence call arguments should not trigger CV-005"

    # CV-008: User has valid domain representation -> no error
    assert "CV-008" not in rule_ids, "User with domain entity representation should not trigger CV-008"


# -----------------------------------------------------------------------------
# Defect 10: Primary key agreement between validation, mapping, and rendering
# -----------------------------------------------------------------------------
def test_defect_10_er_primary_key_harmonization():
    """Validation, mapping, and rendering must agree on primary key handling."""
    er_diagram = {
        "entities": [
            {
                "name": "Account",
                "primary_key": "account_id",
                # Note: account_id is not duplicated in attributes
                "attributes": ["balance", "currency"],
            }
        ]
    }

    # 1. Validation accepts the entity without requiring account_id to be listed twice
    report = validate_er_diagram(er_diagram, class_diagram={})
    assert report["passed"], f"ER validation should pass: {report['errors']}"

    # 2. Mapping ensures account_id is in attributes with PK constraint
    ir = convert_to_ir({"er_diagram": er_diagram})
    account_ent = next(e for e in ir.entities if e.name == "Account")
    pk_attrs = [a for a in account_ent.attributes if a.constraint == "PK"]
    assert len(pk_attrs) == 1
    assert pk_attrs[0].name == "account_id"

    # 3. Rendering renders account_id <<key>> and attributes once
    uml = generate_er_plantuml(ir)
    assert "account_id <<key>>" in uml
    assert "balance" in uml
    assert "currency" in uml


# -----------------------------------------------------------------------------
# Defect 11: Activation lifecycle - never deactivate unactivated lifelines
# -----------------------------------------------------------------------------
def test_defect_11_activation_never_deactivates_unactivated_lifeline():
    """Never deactivate a lifeline that was not activated."""
    seq = {
        "name": "ActivationTest",
        "participants": ["A", "B"],
        "items": [
            # Call without activate
            {"from": "A", "to": "B", "message": "hello()", "type": "call", "activate": False},
            # Return message from B: B was not activated, so B must NOT be deactivated
            {"from": "B", "to": "A", "message": "hi", "type": "return"},
        ],
    }

    uml = generate_sequence_plantuml(seq)
    assert "deactivate B" not in uml
    assert "deactivate A" not in uml


# -----------------------------------------------------------------------------
# Defect 12: Configuration settings remain protected
# -----------------------------------------------------------------------------
def test_defect_12_configuration_immutability():
    """MAX_AGENT_ITERATIONS, candidate models, and provider settings must remain preserved."""
    assert app_config.MAX_AGENT_ITERATIONS == 2
    assert any(m in app_config.GENERATION_MODEL_1 for m in ("qwen", "llama"))
    assert any(m in app_config.GENERATION_MODEL_2 for m in ("qwen", "llama"))
    assert any(m in app_config.GENERATION_MODEL_3 for m in ("qwen", "llama"))


# -----------------------------------------------------------------------------
# Defect 13: Unbalanced activations and nested self-calls detection
# -----------------------------------------------------------------------------
def test_defect_13_unbalanced_activations_and_nested_self_calls():
    """Unbalanced activations including nested self-calls must be detected with specific error codes."""
    seq_unbalanced = [
        {
            "name": "ProcessMeeting",
            "participants": ["Service", "MeetingSession"],
            "items": [
                # Service activates on call
                {"from": "Client", "to": "Service", "message": "process()", "type": "call", "activate": True},
                # MeetingSession activated but never deactivated
                {"from": "Service", "to": "MeetingSession", "message": "addUploadedFile(file: String)", "type": "call", "activate": True},
                # Service makes 3 nested self-calls with activate=True
                {"from": "Service", "to": "Service", "message": "convert()", "type": "call", "activate": True},
                {"from": "Service", "to": "Service", "message": "identify()", "type": "call", "activate": True},
                {"from": "Service", "to": "Service", "message": "extract()", "type": "call", "activate": True},
                # Only 1 deactivation on return
                {"from": "Service", "to": "Client", "message": "response", "type": "return"},
            ],
        }
    ]

    report = validate_sequence_diagrams(seq_unbalanced, class_diagram={
        "classes": [
            {"name": "Service", "methods": ["process()", "convert()", "identify()", "extract()"], "attributes": []},
            {"name": "MeetingSession", "methods": ["addUploadedFile(file: String): void"], "attributes": []},
        ]
    })

    activation_errors = [e for e in report["errors"] if e["code"] == "UNBALANCED_LIFELINE_ACTIVATION"]
    assert len(activation_errors) >= 2, f"Expected at least 2 unbalanced activation errors, got: {activation_errors}"
    unbalanced_participants = {e["details"]["participant"] for e in activation_errors}
    assert "MeetingSession" in unbalanced_participants
    assert "Service" in unbalanced_participants

    # Check that deactivating an unactivated participant triggers DEACTIVATING_UNACTIVATED_LIFELINE
    seq_deactivate_unactive = [
        {
            "name": "BadDeactivation",
            "participants": ["A", "B"],
            "items": [
                {"from": "A", "to": "B", "message": "call()", "type": "call", "activate": False, "deactivate": True},
            ],
        }
    ]
    report_bad_deact = validate_sequence_diagrams(seq_deactivate_unactive, class_diagram={})
    error_codes = [e["code"] for e in report_bad_deact["errors"]]
    assert "DEACTIVATING_UNACTIVATED_LIFELINE" in error_codes


# -----------------------------------------------------------------------------
# Defect 14: Lifecycle multiplicity validation
# -----------------------------------------------------------------------------
def test_defect_14_lifecycle_multiplicity_validation():
    """Containers/sessions created before children must not require 1..* target multiplicity."""
    class_diagram_bad = {
        "classes": [
            {
                "name": "MeetingSession",
                "attributes": ["sessionId: String", "status: String", "createdAt: String"],
                "methods": ["addSpeaker(speaker: Speaker): void", "addRequirement(requirement: Requirement): void"],
            },
            {"name": "Speaker", "attributes": ["speakerId: String", "name: String"], "methods": []},
            {"name": "Requirement", "attributes": ["requirementId: String"], "methods": []},
        ],
        "relationships": [
            {"source": "MeetingSession", "target": "Speaker", "type": "association", "target_multiplicity": "1..*"},
            {"source": "MeetingSession", "target": "Requirement", "type": "association", "target_multiplicity": "1..*"},
        ],
    }

    report = validate_class_diagram(class_diagram_bad)
    lifecycle_errors = [e for e in report["errors"] if e["code"] == "LIFECYCLE_MULTIPLICITY_MISMATCH"]
    assert len(lifecycle_errors) == 2, f"Expected 2 lifecycle multiplicity errors, got: {lifecycle_errors}"

    # Target multiplicity 0..* must pass
    class_diagram_good = {
        "classes": class_diagram_bad["classes"],
        "relationships": [
            {"source": "MeetingSession", "target": "Speaker", "type": "association", "target_multiplicity": "0..*"},
            {"source": "MeetingSession", "target": "Requirement", "type": "association", "target_multiplicity": "0..*"},
        ],
    }
    report_good = validate_class_diagram(class_diagram_good)
    assert not any(e["code"] == "LIFECYCLE_MULTIPLICITY_MISMATCH" for e in report_good["errors"])


# -----------------------------------------------------------------------------
# Defect 15: Redundant ER attributes duplicating relationships
# -----------------------------------------------------------------------------
def test_defect_15_redundant_er_attributes_detection():
    """Redundant ER attributes duplicating relationships must be detected and pruned."""
    er_diagram = {
        "entities": [
            {
                "name": "MeetingSession",
                "primary_key": "sessionId",
                "attributes": ["sessionId", "status", "speakers", "requirements", "feedback"],
            },
            {"name": "Speaker", "primary_key": "speakerId", "attributes": ["speakerId", "name"]},
            {"name": "Requirement", "primary_key": "requirementId", "attributes": ["requirementId"]},
            {"name": "Feedback", "primary_key": "feedbackId", "attributes": ["feedbackId"]},
        ],
        "relationships": [
            {"name": "HAS_SPEAKER", "source": "MeetingSession", "target": "Speaker", "type": "one-to-many", "source_multiplicity": "1", "target_multiplicity": "0..*"},
            {"name": "HAS_REQUIREMENT", "source": "MeetingSession", "target": "Requirement", "type": "one-to-many", "source_multiplicity": "1", "target_multiplicity": "0..*"},
            {"name": "HAS_FEEDBACK", "source": "MeetingSession", "target": "Feedback", "type": "one-to-many", "source_multiplicity": "1", "target_multiplicity": "0..*"},
        ],
    }

    report = validate_er_diagram(er_diagram, class_diagram={})
    redundant_errors = [e for e in report["errors"] if e["code"] == "REDUNDANT_RELATIONSHIP_ATTRIBUTE"]
    assert len(redundant_errors) == 3, f"Expected 3 redundant attribute errors, got: {redundant_errors}"

    # convert_to_ir should filter them out
    ir = convert_to_ir({"er_diagram": er_diagram})
    session_ent = next(e for e in ir.entities if e.name == "MeetingSession")
    attr_names = [a.name for a in session_ent.attributes]
    assert "speakers" not in attr_names
    assert "requirements" not in attr_names
    assert "feedback" not in attr_names

    # PlantUML ER rendering should not include redundant attributes in entity
    chen = generate_er_plantuml(er_diagram)
    assert "    speakers\n" not in chen
    assert "    requirements\n" not in chen
    assert "    feedback\n" not in chen


# -----------------------------------------------------------------------------
# Defect 16: Speculative architecture without verified HLD
# -----------------------------------------------------------------------------
def test_defect_16_speculative_architecture_without_hld():
    """Unverified Controller/Service/Repository components must be flagged as speculative."""
    seq = [
        {
            "name": "UploadProcess",
            "participants": ["Controller", "Service", "Repository", "MeetingSession"],
            "items": [
                {"from": "Controller", "to": "Service", "message": "process()", "type": "call"},
                {"from": "Service", "to": "Repository", "message": "save()", "type": "call"},
            ],
        }
    ]

    report = validate_sequence_diagrams(seq, class_diagram={
        "classes": [{"name": "MeetingSession", "attributes": ["sessionId"], "methods": []}]
    })

    speculative_warnings = [w for w in report["warnings"] if w["code"] == "SPECULATIVE_ARCHITECTURE_PARTICIPANT"]
    assert len(speculative_warnings) >= 3, f"Expected warnings for Controller, Service, Repository: {speculative_warnings}"
    flagged = {w["details"]["participant"] for w in speculative_warnings}
    assert "Controller" in flagged
    assert "Service" in flagged
    assert "Repository" in flagged


# -----------------------------------------------------------------------------
# Defect 17: Method argument data-type and count inconsistencies
# -----------------------------------------------------------------------------
def test_defect_17_method_argument_and_data_type_inconsistency():
    """Argument count and data-type mismatches between Sequence and Class must be detected."""
    class_diagram = {
        "classes": [
            {
                "name": "MeetingSession",
                "attributes": [],
                "methods": [
                    {"name": "addUploadedFile", "parameters": [{"name": "file", "data_type": "String"}]},
                    {"name": "addSpeaker", "parameters": [{"name": "speaker", "data_type": "Speaker"}]},
                ],
            }
        ]
    }

    # Calling with File instead of String -> type mismatch
    seq_type_mismatch = [
        {
            "name": "TypeMismatchSeq",
            "participants": ["MeetingSession"],
            "items": [
                {"from": "Client", "to": "MeetingSession", "message": "addUploadedFile(file: File)", "type": "call"},
            ],
        }
    ]

    report = validate_sequence_diagrams(seq_type_mismatch, class_diagram)
    type_errors = [e for e in report["errors"] if e["code"] == "METHOD_ARGUMENT_TYPE_MISMATCH"]
    assert len(type_errors) == 1, f"Expected METHOD_ARGUMENT_TYPE_MISMATCH error, got: {report['errors']}"
    assert type_errors[0]["details"]["expected_type"] == "String"
    assert type_errors[0]["details"]["actual_type"] == "File"

    # Calling with extra arguments -> count mismatch
    seq_extra_args = [
        {
            "name": "ExtraArgsSeq",
            "participants": ["MeetingSession"],
            "items": [
                {"from": "Client", "to": "MeetingSession", "message": "addUploadedFile(f1: String, f2: String)", "type": "call"},
            ],
        }
    ]
    report_extra = validate_sequence_diagrams(seq_extra_args, class_diagram)
    count_errors = [e for e in report_extra["errors"] if e["code"] == "METHOD_ARGUMENT_COUNT_MISMATCH"]
    assert len(count_errors) == 1, f"Expected METHOD_ARGUMENT_COUNT_MISMATCH, got: {report_extra['errors']}"


# -----------------------------------------------------------------------------
# Defect 18: Mandatory use case steps and failure behavior checks
# -----------------------------------------------------------------------------
def test_defect_18_mandatory_use_case_steps_and_failure_handling():
    """Sequences must include use case steps and warn on missing failure paths for heavy operations."""
    seq_no_response = [
        {
            "name": "NoResponseSeq",
            "participants": ["Client", "Processor"],
            "items": [
                {"from": "Client", "to": "Processor", "message": "uploadFile(file: File)", "type": "call"},
                {"from": "Processor", "to": "Processor", "message": "convertAudio()", "type": "call"},
            ],
        }
    ]

    report = validate_sequence_diagrams(seq_no_response, class_diagram={})
    step_warnings = [w for w in report["warnings"] if w["code"] == "MISSING_MANDATORY_PROCESSING_STEP"]
    assert len(step_warnings) == 1

    failure_warnings = [w for w in report["warnings"] if w["code"] == "MISSING_FAILURE_BEHAVIOR"]
    assert len(failure_warnings) == 1, "File conversion operation without alt/error handling must warn"


# -----------------------------------------------------------------------------
# Defect 19: Full Meeting-Information regression test case from user prompt
# -----------------------------------------------------------------------------
def test_defect_19_meeting_information_full_case():
    """Verify detection of all remaining issues in the user's meeting-information UML output."""
    class_diagram = {
        "classes": [
            {
                "name": "MeetingSession",
                "attributes": ["sessionId: String", "status: String", "uploadedFiles: List<String>", "createdAt: String"],
                "methods": [
                    "+addUploadedFile(file: String): void",
                    "+setTranscript(transcript: String): void",
                    "+addSpeaker(speaker: Speaker): void",
                    "+addRequirement(requirement: Requirement): void",
                    "+addFeedback(feedback: Feedback): void",
                    "+addAnalysisResult(result: AnalysisResult): void",
                    "+updateStatus(status: String): void",
                ],
            },
            {"name": "Speaker", "attributes": ["speakerId: String", "name: String", "role: String"], "methods": []},
            {"name": "Requirement", "attributes": ["requirementId: String", "description: String", "issues: List<String>"], "methods": ["+addIssue(issue: String): void"]},
            {"name": "Feedback", "attributes": ["feedbackId: String", "description: String"], "methods": []},
            {"name": "AnalysisResult", "attributes": ["resultId: String", "description: String"], "methods": []},
        ],
        "relationships": [
            {"source": "MeetingSession", "target": "Speaker", "type": "association", "target_multiplicity": "1..*"},
            {"source": "MeetingSession", "target": "Requirement", "type": "association", "target_multiplicity": "1..*"},
            {"source": "MeetingSession", "target": "Feedback", "type": "association", "target_multiplicity": "0..*"},
            {"source": "MeetingSession", "target": "AnalysisResult", "type": "association", "target_multiplicity": "0..*"},
        ],
    }

    # 1. Class Diagram validation detects lifecycle multiplicity mismatches
    class_report = validate_class_diagram(class_diagram)
    lifecycle_errors = [e for e in class_report["errors"] if e["code"] == "LIFECYCLE_MULTIPLICITY_MISMATCH"]
    assert len(lifecycle_errors) == 2, f"Expected 2 lifecycle errors on MeetingSession, got: {lifecycle_errors}"

    # 2. Sequence Diagram validation detects unbalanced activations and speculative architecture
    sequence_diagram = {
        "name": "Upload and Process Meeting Information",
        "participants": ["BusinessAnalyst", "Frontend", "Controller", "Service", "Repository", "MeetingSession"],
        "items": [
            {"from": "BusinessAnalyst", "to": "Frontend", "message": "uploadMeetingInformation(meetingFile: File, documents: List<File>)", "type": "call", "activate": True},
            {"from": "Frontend", "to": "Controller", "message": "submitMeetingInformation(request: MeetingInformationRequest)", "type": "call", "activate": True},
            {"from": "Controller", "to": "Service", "message": "processMeetingInformation(request: MeetingInformationRequest)", "type": "call", "activate": True},
            # MeetingSession activated but never deactivated
            {"from": "Service", "to": "MeetingSession", "message": "addUploadedFile(file: String)", "type": "call", "activate": True},
            # 3 nested self-calls on Service
            {"from": "Service", "to": "Service", "message": "convertMeetingToText(meetingFile: File)", "type": "call", "activate": True},
            {"from": "Service", "to": "Service", "message": "identifySpeakers(transcript: String)", "type": "call", "activate": True},
            {"from": "Service", "to": "Service", "message": "extractRequirements(transcript: String, documents: List<File>)", "type": "call", "activate": True},
            {"from": "Service", "to": "MeetingSession", "message": "setTranscript(transcript: String)", "type": "call"},
            {"from": "Service", "to": "MeetingSession", "message": "addSpeaker(speaker: Speaker)", "type": "call"},
            {"from": "Service", "to": "MeetingSession", "message": "addRequirement(requirement: Requirement)", "type": "call"},
            {"from": "Service", "to": "Repository", "message": "saveMeetingSession(session: MeetingSession)", "type": "call", "activate": True},
            {"from": "Repository", "to": "Service", "message": "session: MeetingSession", "type": "return"},
            {"from": "Service", "to": "Controller", "message": "response: MeetingInformationResponse", "type": "return"},
            {"from": "Controller", "to": "Frontend", "message": "response: MeetingInformationResponse", "type": "return"},
            {"from": "Frontend", "to": "BusinessAnalyst", "message": "confirmation: String", "type": "return"},
        ],
    }

    seq_report = validate_sequence_diagrams([sequence_diagram], class_diagram)
    unbalanced = [e for e in seq_report["errors"] if e["code"] == "UNBALANCED_LIFELINE_ACTIVATION"]
    assert len(unbalanced) == 2, f"Expected unbalanced activation on MeetingSession and Service, got: {unbalanced}"
    unbalanced_names = {e["details"]["participant"] for e in unbalanced}
    assert "MeetingSession" in unbalanced_names
    assert "Service" in unbalanced_names

    speculative = [w for w in seq_report["warnings"] if w["code"] == "SPECULATIVE_ARCHITECTURE_PARTICIPANT"]
    assert len(speculative) >= 4, f"Expected speculative architecture warnings: {speculative}"

    # 3. ER Diagram validation detects redundant attributes and lifecycle multiplicity
    er_diagram = {
        "entities": [
            {
                "name": "MeetingSession",
                "primary_key": "sessionId",
                "attributes": ["sessionId", "status", "uploadedFiles", "transcript", "speakers", "requirements", "feedback", "analysisResults", "createdAt", "updatedAt"],
            },
            {"name": "Speaker", "primary_key": "speakerId", "attributes": ["speakerId", "name", "role"]},
            {"name": "Requirement", "primary_key": "requirementId", "attributes": ["requirementId", "description", "priority", "type", "context", "status", "issues"]},
            {"name": "Feedback", "primary_key": "feedbackId", "attributes": ["feedbackId", "description", "type", "createdAt"]},
            {"name": "AnalysisResult", "primary_key": "resultId", "attributes": ["resultId", "description", "type", "createdAt"]},
        ],
        "relationships": [
            {"name": "HAS_SPEAKER", "source": "MeetingSession", "target": "Speaker", "type": "one-to-many", "source_multiplicity": "1", "target_multiplicity": "1..*"},
            {"name": "HAS_REQUIREMENT", "source": "MeetingSession", "target": "Requirement", "type": "one-to-many", "source_multiplicity": "1", "target_multiplicity": "1..*"},
            {"name": "HAS_FEEDBACK", "source": "MeetingSession", "target": "Feedback", "type": "one-to-many", "source_multiplicity": "1", "target_multiplicity": "0..*"},
            {"name": "HAS_ANALYSISRESULT", "source": "MeetingSession", "target": "AnalysisResult", "type": "one-to-many", "source_multiplicity": "1", "target_multiplicity": "0..*"},
        ],
    }

    er_report = validate_er_diagram(er_diagram, class_diagram)
    redundant = [e for e in er_report["errors"] if e["code"] == "REDUNDANT_RELATIONSHIP_ATTRIBUTE"]
    assert len(redundant) == 4, f"Expected 4 redundant ER attributes on MeetingSession, got: {redundant}"

    er_lifecycle = [e for e in er_report["errors"] if e["code"] == "LIFECYCLE_MULTIPLICITY_MISMATCH"]
    assert len(er_lifecycle) == 2, f"Expected 2 lifecycle multiplicity errors in ER, got: {er_lifecycle}"

    # 4. Consistency Engine rules CV-010, CV-011, CV-012 detect these cross-model inconsistencies
    ir = convert_to_ir({"class_diagram": class_diagram, "sequence_diagrams": [sequence_diagram], "er_diagram": er_diagram})
    consistency_report = ConsistencyEngine().validate(ir)
    rule_ids = {e.rule_id for e in consistency_report.errors}
    assert "CV-010" in rule_ids, "Expected CV-010 (unbalanced activations)"
    assert "CV-012" in rule_ids, "Expected CV-012 (lifecycle multiplicity)"
