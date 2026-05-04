from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    ),
    Column("assigned_at", DateTime, default=datetime.utcnow),
)

# association
group_applicants = Table(
    "group_applicants",
    Base.metadata,
    Column(
        "group_id",
        UUID(as_uuid=True),
        ForeignKey("applicant_groups.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "applicant_id",
        UUID(as_uuid=True),
        ForeignKey("applicants.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
