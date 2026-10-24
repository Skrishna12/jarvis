from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from jarvis.core.clock import utc_now
from jarvis.core.dates import parse_datetime
from jarvis.db.models import Task
from jarvis.memory.errors import ValidationError

STATUSES = ("open", "in_progress", "done", "cancelled")
PRIORITIES = ("low", "medium", "high")


class TaskNotFoundError(LookupError):
    pass


@dataclass(frozen=True)
class TaskRecord:
    id: str
    title: str
    description: str
    status: str
    priority: str
    parent_id: str | None
    due_at: datetime | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


def _to_record(row: Task) -> TaskRecord:
    return TaskRecord(
        id=row.id,
        title=row.title,
        description=row.description,
        status=row.status,
        priority=row.priority,
        parent_id=row.parent_id,
        due_at=row.due_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
        completed_at=row.completed_at,
    )


class TaskStore:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        title: str,
        *,
        description: str = "",
        priority: str = "medium",
        parent_id: str | None = None,
        due_at: str | None = None,
    ) -> TaskRecord:
        title = title.strip()
        if not title:
            raise ValidationError("Task title cannot be empty.")
        priority = _parse_choice(priority, PRIORITIES, "priority")
        if parent_id:
            self.get(parent_id)
        now = utc_now()
        row = Task(
            id=str(uuid4()),
            title=title,
            description=description.strip(),
            status="open",
            priority=priority,
            parent_id=parent_id or None,
            due_at=parse_datetime(due_at) if due_at else None,
            created_at=now,
            updated_at=now,
            completed_at=None,
        )
        self._session.add(row)
        self._session.flush()
        return _to_record(row)

    def get(self, task_id: str) -> TaskRecord:
        row = self._session.get(Task, task_id)
        if row is None:
            raise TaskNotFoundError(
                f"No task {task_id!r}. Use task.list to see ids."
            )
        return _to_record(row)

    def list(
        self,
        *,
        status: str | None = None,
        parent_id: str | None = None,
    ) -> list[TaskRecord]:
        stmt = select(Task).order_by(Task.priority.desc(), Task.created_at)
        if status:
            stmt = stmt.where(Task.status == _parse_choice(status, STATUSES, "status"))
        if parent_id:
            stmt = stmt.where(Task.parent_id == parent_id)
        return [_to_record(row) for row in self._session.scalars(stmt).all()]

    def update(
        self,
        task_id: str,
        *,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        due_at: str | None = None,
    ) -> TaskRecord:
        row = self._require(task_id)
        if title is not None:
            if not title.strip():
                raise ValidationError("Task title cannot be empty.")
            row.title = title.strip()
        if description is not None:
            row.description = description.strip()
        if status is not None:
            row.status = _parse_choice(status, STATUSES, "status")
            if row.status == "done" and row.completed_at is None:
                row.completed_at = utc_now()
            if row.status != "done":
                row.completed_at = None
        if priority is not None:
            row.priority = _parse_choice(priority, PRIORITIES, "priority")
        if due_at is not None:
            row.due_at = parse_datetime(due_at) if due_at.strip() else None
        row.updated_at = utc_now()
        self._session.flush()
        return _to_record(row)

    def complete(self, task_id: str) -> TaskRecord:
        return self.update(task_id, status="done")

    def prioritize(self, task_id: str, priority: str) -> TaskRecord:
        return self.update(task_id, priority=priority)

    def add_subtask(self, parent_id: str, title: str, **kwargs) -> TaskRecord:
        self.get(parent_id)
        return self.create(title, parent_id=parent_id, **kwargs)

    def delete(self, task_id: str) -> TaskRecord:
        row = self._require(task_id)
        children = self._session.scalars(
            select(Task).where(Task.parent_id == task_id)
        ).all()
        if children:
            raise ValidationError(
                f"Task {task_id} has {len(children)} subtask(s). "
                "Delete or move them first."
            )
        record = _to_record(row)
        self._session.delete(row)
        self._session.flush()
        return record

    def _require(self, task_id: str) -> Task:
        row = self._session.get(Task, task_id)
        if row is None:
            raise TaskNotFoundError(
                f"No task {task_id!r}. Use task.list to see ids."
            )
        return row


def _parse_choice(raw: str, allowed: tuple[str, ...], field: str) -> str:
    value = raw.strip().lower()
    if value not in allowed:
        raise ValidationError(
            f"Unknown {field} {raw!r}. Use one of: {', '.join(allowed)}."
        )
    return value
