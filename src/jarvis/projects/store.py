from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from jarvis.core.clock import utc_now
from jarvis.db.models import Project
from jarvis.memory.errors import ValidationError

STATUSES = ("active", "paused", "done")


class ProjectNotFoundError(LookupError):
    pass


@dataclass(frozen=True)
class ProjectRecord:
    id: str
    name: str
    status: str
    description: str
    created_at: datetime
    updated_at: datetime


def _to_record(row: Project) -> ProjectRecord:
    return ProjectRecord(
        id=row.id,
        name=row.name,
        status=row.status,
        description=row.description,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class ProjectStore:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, name: str, *, description: str = "", status: str = "active") -> ProjectRecord:
        name = name.strip()
        if not name:
            raise ValidationError("Project name cannot be empty.")
        status = status.strip().lower()
        if status not in STATUSES:
            raise ValidationError(f"Unknown status {status!r}. Use {', '.join(STATUSES)}.")
        existing = self._session.scalar(select(Project).where(Project.name == name))
        if existing is not None:
            raise ValidationError(f"A project named {name!r} already exists.")
        now = utc_now()
        row = Project(
            id=str(uuid4()),
            name=name,
            status=status,
            description=description.strip(),
            created_at=now,
            updated_at=now,
        )
        self._session.add(row)
        self._session.flush()
        return _to_record(row)

    def get(self, project_id: str) -> ProjectRecord:
        row = self._session.get(Project, project_id)
        if row is None:
            raise ProjectNotFoundError(
                f"No project {project_id!r}. Use project.list."
            )
        return _to_record(row)

    def list(self, *, status: str | None = None) -> list[ProjectRecord]:
        stmt = select(Project).order_by(Project.name)
        if status:
            stmt = stmt.where(Project.status == status)
        return [_to_record(row) for row in self._session.scalars(stmt).all()]

    def update(self, project_id: str, *, status: str | None = None, description: str | None = None) -> ProjectRecord:
        row = self._session.get(Project, project_id)
        if row is None:
            raise ProjectNotFoundError(f"No project {project_id!r}.")
        if status is not None:
            value = status.strip().lower()
            if value not in STATUSES:
                raise ValidationError(f"Unknown status {status!r}.")
            row.status = value
        if description is not None:
            row.description = description.strip()
        row.updated_at = utc_now()
        self._session.flush()
        return _to_record(row)
