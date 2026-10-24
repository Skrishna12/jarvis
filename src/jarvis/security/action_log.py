from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from jarvis.core.clock import utc_now
from jarvis.db.models import ActionLog
from jarvis.security.levels import PermissionLevel
from jarvis.security.payload import dumps


class ActionLogger:
    def __init__(self, session: Session) -> None:
        self._session = session

    def record(
        self,
        *,
        agent: str,
        action: str,
        level: PermissionLevel,
        payload: dict,
        result: str,
        error_message: str | None = None,
    ) -> ActionLog:
        row = ActionLog(
            id=str(uuid4()),
            created_at=utc_now(),
            agent=agent,
            action=action,
            permission_level=int(level),
            payload_json=dumps(payload),
            result=result,
            error_message=error_message,
        )
        self._session.add(row)
        self._session.flush()
        return row

    def recent(self, limit: int = 20) -> list[ActionLog]:
        if limit < 1:
            limit = 1
        rows = self._session.scalars(
            select(ActionLog).order_by(ActionLog.created_at.desc()).limit(limit)
        ).all()
        return list(rows)
