from sqlalchemy import Column, Integer, Text, String, DateTime
from sqlalchemy.sql import func

from database import Base


class Project(Base):
    __tablename__ = "lld_projects"

    id = Column(Integer, primary_key=True, index=True)

    project_name = Column(String(255), nullable=True)
    project_description = Column(Text, nullable=True)

    agent1_input = Column(Text, nullable=False)
    agent2_input = Column(Text, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )