"""Inbox labels for this phase.

Urgency is separate from topic: "Urgent" in the long-term vision is
modeled as urgency=urgent, not as a topic category.
"""

from __future__ import annotations

from enum import StrEnum


class EmailCategory(StrEnum):
    JOB = "Job"
    WORK = "Work"
    INTERVIEW = "Interview"
    EDUCATION = "Education"
    FINANCE = "Finance"
    BILLS = "Bills"
    ORDERS = "Orders"
    PERSONAL = "Personal"
    NOTIFICATIONS = "Notifications"
    OTHER = "Other"


class EmailUrgency(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    URGENT = "urgent"


TOPIC_LABELS = [c.value for c in EmailCategory]
URGENCY_LABELS = [u.value for u in EmailUrgency]
