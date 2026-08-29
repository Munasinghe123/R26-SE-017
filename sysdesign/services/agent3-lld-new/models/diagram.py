from sqlalchemy import  Column, Integer, Enum, Text, ForeignKey, DateTime, Boolean, String
from sqlalchemy.sql import func
from database import Base


class Diagram(Base):
    __tablename__ = "diagrams"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False,
        index=True
    )

    # Generation run
    generation_run_id = Column(
        Integer,
        ForeignKey("generation_runs.id"),
        nullable=False,
        index=True
    )

    candidate_id = Column(
        Integer,
        ForeignKey("candidates.id"),
        nullable=False,
        index=True
    )

    # Diagram type
    diagram_type = Column(
        Enum(
            "class",
            "sequence",
            "er",
            name="diagram_type_enum"
        ),
        nullable=False
    )

    # PlantUML source
    plantuml_code = Column(
        Text,
        nullable=False
    )

    # Rendered diagram
    cloudinary_url = Column(
        Text,
        nullable=True
    )

    # Optional structured representation / IR
    structured_data = Column(
        Text,
        nullable=True
    )

    # Whether this diagram belongs to the selected candidate
    is_selected = Column(
        Boolean,
        nullable=False,
        default=False
    )

    # Whether this is the final reconciled diagram
    is_final = Column(
        Boolean,
        nullable=False,
        default=False
    )

    # Diagram generation model
    model_name = Column(
        String(150),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )