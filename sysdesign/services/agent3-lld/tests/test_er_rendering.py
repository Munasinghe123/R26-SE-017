import pytest
from utils.irGenerator import generate_er_plantuml, is_invalid_relationship_name
from utils.irMapper import convert_to_ir
from schemas.ir_schema import EntityRelationship


def test_is_invalid_relationship_name():
    # Cardinality labels must be rejected
    assert is_invalid_relationship_name("one-to-many") is True
    assert is_invalid_relationship_name("one-to-one") is True
    assert is_invalid_relationship_name("many-to-many") is True
    assert is_invalid_relationship_name("1:N") is True
    assert is_invalid_relationship_name("1..*") is True
    assert is_invalid_relationship_name("has-many") is True
    assert is_invalid_relationship_name("") is True
    assert is_invalid_relationship_name(None) is True

    # Semantic business verbs must be accepted
    assert is_invalid_relationship_name("OWNS") is False
    assert is_invalid_relationship_name("CONTAINS") is False
    assert is_invalid_relationship_name("PLACES") is False
    assert is_invalid_relationship_name("ENROLLS_IN") is False
    assert is_invalid_relationship_name("BELONGS_TO") is False


def test_generate_er_plantuml_renders_semantic_relationship_names_and_separate_cardinality():
    er_diagram = {
        "entities": [
            {
                "name": "User",
                "attributes": ["user_id", "email"],
                "primary_key": "user_id"
            },
            {
                "name": "Project",
                "attributes": ["project_id", "title"],
                "primary_key": "project_id"
            },
            {
                "name": "RequirementDocument",
                "attributes": ["doc_id", "name"],
                "primary_key": "doc_id"
            }
        ],
        "relationships": [
            {
                "name": "OWNS",
                "source": "User",
                "target": "Project",
                "type": "one-to-many",
                "source_multiplicity": "1",
                "target_multiplicity": "0..*"
            },
            {
                "name": "CONTAINS",
                "source": "Project",
                "target": "RequirementDocument",
                "type": "one-to-many",
                "source_multiplicity": "1",
                "target_multiplicity": "1..*"
            }
        ]
    }

    plantuml = generate_er_plantuml(er_diagram)

    # Must contain semantic relationship labels
    assert 'relationship "OWNS" as REL_0' in plantuml
    assert 'relationship "CONTAINS" as REL_1' in plantuml

    # Must NOT contain cardinality labels as relationship names
    assert 'relationship "one-to-many"' not in plantuml

    # Must render Chen cardinalities separately on connectors
    assert "REL_0-1- USER" in plantuml
    assert "REL_0-(0,N)- PROJECT" in plantuml
    assert "REL_1-1- PROJECT" in plantuml
    assert "REL_1-(1,N)- REQUIREMENTDOCUMENT" in plantuml


def test_generate_er_plantuml_handles_cardinality_label_in_name_gracefully():
    er_diagram = {
        "entities": [
            {"name": "User", "attributes": ["id"], "primary_key": "id"},
            {"name": "Project", "attributes": ["id"], "primary_key": "id"}
        ],
        "relationships": [
            {
                "name": "one-to-many",
                "source": "User",
                "target": "Project",
                "type": "one-to-many"
            }
        ]
    }

    plantuml = generate_er_plantuml(er_diagram)

    # Must NOT display "one-to-many" as relationship name
    assert 'relationship "one-to-many"' not in plantuml
    assert 'relationship "RELATIONSHIP" as REL_0' in plantuml


def test_ir_mapper_preserves_er_relationship_fields():
    parsed_json = {
        "er_diagram": {
            "entities": [
                {"name": "User", "attributes": ["user_id"], "primary_key": "user_id"},
                {"name": "Project", "attributes": ["project_id"], "primary_key": "project_id"}
            ],
            "relationships": [
                {
                    "name": "OWNS",
                    "source": "User",
                    "target": "Project",
                    "type": "one-to-many",
                    "source_multiplicity": "1",
                    "target_multiplicity": "0..*"
                }
            ]
        }
    }

    ir = convert_to_ir(parsed_json)
    user_entity = next(e for e in ir.entities if e.name == "User")
    rel = user_entity.relationships[0]

    assert isinstance(rel, EntityRelationship)
    assert rel.name == "OWNS"
    assert rel.target == "Project"
    assert rel.source == "User"
    assert rel.rel_type == "one-to-many"
    assert rel.source_multiplicity == "1"
    assert rel.target_multiplicity == "0..*"
