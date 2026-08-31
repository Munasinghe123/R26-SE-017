"""
Regression Tests for Sequence Diagram Generation and PlantUML Rendering
"""
from utils.irGenerator import generate_sequence_plantuml
from utils.sequence_normalizer import normalize_sequence_diagram


def test_participant_role_mapping_and_footbox():
    sequence = {
        "name": "Role Mapping Test",
        "participants": ["Customer", "FrontendUI", "OrderController", "OrderService", "Order", "OrderRepository", "PaymentGateway"],
        "participant_types": {
            "Customer": "actor",
            "FrontendUI": "boundary",
            "OrderController": "controller",
            "OrderService": "service",
            "Order": "entity",
            "OrderRepository": "repository",
            "PaymentGateway": "external_system",
        },
        "messages": [
            {"from": "Customer", "to": "FrontendUI", "message": "checkout()", "type": "call"},
            {"from": "FrontendUI", "to": "OrderController", "message": "process()", "type": "call"},
            {"from": "OrderController", "to": "OrderService", "message": "execute()", "type": "call"},
            {"from": "OrderService", "to": "Order", "message": "calculate()", "type": "call"},
            {"from": "OrderService", "to": "OrderRepository", "message": "save()", "type": "call"},
            {"from": "OrderService", "to": "PaymentGateway", "message": "pay()", "type": "call"},
        ],
    }

    plantuml = generate_sequence_plantuml(sequence)

    # 1. Hide footbox
    assert "hide footbox" in plantuml

    # 2. PlantUML keywords mapped correctly
    assert 'actor "Customer" as Customer' in plantuml
    assert 'boundary "FrontendUI" as FrontendUI' in plantuml
    assert 'control "OrderController" as OrderController' in plantuml
    assert 'control "OrderService" as OrderService' in plantuml
    assert 'entity "Order" as Order' in plantuml
    assert 'participant "OrderRepository" as OrderRepository' in plantuml
    assert 'participant "PaymentGateway" as PaymentGateway' in plantuml


def test_call_and_return_message_arrows():
    sequence = {
        "name": "Arrow Test",
        "participants": ["FrontendUI", "OrderController"],
        "participant_types": {
            "FrontendUI": "boundary",
            "OrderController": "controller",
        },
        "messages": [
            {"from": "FrontendUI", "to": "OrderController", "message": "submitCheckout(req)", "type": "call"},
            {"from": "OrderController", "to": "FrontendUI", "message": "successResponse(order_id)", "type": "return"},
        ],
    }

    plantuml = generate_sequence_plantuml(sequence)

    # Call arrow ->
    assert "FrontendUI -> OrderController: submitCheckout(req)" in plantuml
    # Return arrow -->
    assert "OrderController --> FrontendUI: successResponse(order_id)" in plantuml


def test_loop_rendering_and_causal_ordering():
    sequence = {
        "name": "Checkout Loop Test",
        "participants": ["Customer", "FrontendUI", "OrderController", "DatabaseRepository"],
        "participant_types": {
            "Customer": "actor",
            "FrontendUI": "boundary",
            "OrderController": "controller",
            "DatabaseRepository": "repository",
        },
        "items": [
            {"from": "Customer", "to": "FrontendUI", "message": "submitCheckout(request)", "type": "call"},
            {"from": "FrontendUI", "to": "OrderController", "message": "submitCheckout(request)", "type": "call"},
            {"from": "OrderController", "to": "DatabaseRepository", "message": "createOrder(order)", "type": "call"},
            {
                "type": "loop",
                "condition": "for each cart item",
                "items": [
                    {"from": "OrderController", "to": "DatabaseRepository", "message": "createCartItem(cartItem)", "type": "call"}
                ],
            },
            {"from": "OrderController", "to": "FrontendUI", "message": "successResponse(order_id)", "type": "return"},
        ],
    }

    plantuml = generate_sequence_plantuml(sequence)

    # Assert loop syntax and nesting
    assert "loop [for each cart item]" in plantuml
    assert "OrderController -> DatabaseRepository: createCartItem(cartItem)" in plantuml
    assert "end" in plantuml

    # Assert causal ordering: createOrder -> loop -> successResponse
    pos_create_order = plantuml.find("createOrder")
    pos_loop = plantuml.find("loop [for each cart item]")
    pos_create_item = plantuml.find("createCartItem")
    pos_success = plantuml.find("successResponse")

    assert pos_create_order < pos_loop < pos_create_item < pos_success


def test_unused_participant_removal():
    sequence = {
        "name": "Unused Participant Test",
        "participants": ["Customer", "FrontendUI", "UnusedService"],
        "participant_types": {
            "Customer": "actor",
            "FrontendUI": "boundary",
            "UnusedService": "service",
        },
        "messages": [
            {"from": "Customer", "to": "FrontendUI", "message": "login()", "type": "call"}
        ],
    }

    normalized = normalize_sequence_diagram(sequence)
    assert "UnusedService" not in normalized["participants"]

    plantuml = generate_sequence_plantuml(sequence)
    assert "UnusedService" not in plantuml


def test_parameter_preservation():
    sequence = {
        "name": "Parameters Test",
        "participants": ["Customer", "FrontendUI"],
        "messages": [
            {"from": "Customer", "to": "FrontendUI", "message": "submitCheckout(customer_id, cart_items)", "type": "call"}
        ],
    }

    plantuml = generate_sequence_plantuml(sequence)
    assert "submitCheckout(customer_id, cart_items)" in plantuml
