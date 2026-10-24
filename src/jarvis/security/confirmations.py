from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from jarvis.core.clock import utc_now
from jarvis.db.models import PendingConfirmation
from jarvis.security.errors import ConfirmationError
from jarvis.security.levels import PermissionLevel
from jarvis.security.payload import dumps, loads

STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_DENIED = "denied"


class ConfirmationStore:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        tool_name: str,
        payload: dict,
        level: PermissionLevel,
        agent: str,
    ) -> PendingConfirmation:
        row = PendingConfirmation(
            id=str(uuid4()),
            tool_name=tool_name,
            payload_json=dumps(payload),
            permission_level=int(level),
            agent=agent,
            status=STATUS_PENDING,
            created_at=utc_now(),
        )
        self._session.add(row)
        self._session.flush()
        return row

    def get(self, confirmation_id: str) -> PendingConfirmation:
        row = self._session.get(PendingConfirmation, confirmation_id)
        if row is None:
            raise ConfirmationError(
                f"No confirmation {confirmation_id!r}. "
                "Run `jarvis confirm list` to see pending actions."
            )
        return row

    def latest_pending(self) -> PendingConfirmation | None:
        return self._session.scalar(
            select(PendingConfirmation)
            .where(PendingConfirmation.status == STATUS_PENDING)
            .order_by(PendingConfirmation.created_at.desc())
        )

    def list_pending(self) -> list[PendingConfirmation]:
        return list(
            self._session.scalars(
                select(PendingConfirmation)
                .where(PendingConfirmation.status == STATUS_PENDING)
                .order_by(PendingConfirmation.created_at.desc())
            ).all()
        )

    def payload(self, row: PendingConfirmation) -> dict:
        return loads(row.payload_json)

    def mark(self, confirmation_id: str, status: str) -> PendingConfirmation:
        row = self.get(confirmation_id)
        if row.status != STATUS_PENDING:
            raise ConfirmationError(
                f"Confirmation {confirmation_id} is already {row.status}."
            )
        row.status = status
        self._session.flush()
        return row
