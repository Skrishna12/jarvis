"""Topic, urgency, and deadline hints from subject/body."""

from __future__ import annotations

import re
from dataclasses import dataclass

from jarvis.email.categories import EmailCategory, EmailUrgency
from jarvis.llm.base import LLMProvider
from jarvis.llm.errors import LlmError
from jarvis.llm.fake import FakeProvider
from jarvis.llm.types import ChatMessage

_KEYWORDS: list[tuple[EmailCategory, tuple[str, ...]]] = [
    (EmailCategory.INTERVIEW, ("interview", "onsite", "recruiter screen")),
    (EmailCategory.JOB, ("job application", "offer letter", "candidate")),
    (EmailCategory.BILLS, ("invoice", "bill due", "payment overdue")),
    (EmailCategory.FINANCE, ("bank", "statement", "tax", "payroll")),
    (EmailCategory.ORDERS, ("your order", "shipped", "tracking number")),
    (EmailCategory.EDUCATION, ("assignment", "university", "course", "tuition")),
    (EmailCategory.WORK, ("standup", "sprint", "jira", "pull request")),
    (EmailCategory.NOTIFICATIONS, ("unsubscribe", "noreply", "no-reply")),
    (EmailCategory.PERSONAL, ("family", "birthday", "dinner")),
]

_URGENT = ("urgent", "asap", "immediately", "action required", "final notice")
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2})?)?")


@dataclass(frozen=True)
class EmailHints:
    category: EmailCategory
    urgency: EmailUrgency
    deadline_note: str | None


def hint(subject: str, body: str) -> EmailHints:
    blob = f"{subject}\n{body}".lower()
    category = EmailCategory.OTHER
    for cat, words in _KEYWORDS:
        if any(word in blob for word in words):
            category = cat
            break
    urgency = EmailUrgency.NORMAL
    if any(word in blob for word in _URGENT) or category is EmailCategory.INTERVIEW:
        urgency = EmailUrgency.URGENT
    match = _DATE.search(f"{subject} {body}")
    deadline = match.group(0).replace(" ", "T") if match else None
    if deadline and category is EmailCategory.INTERVIEW:
        deadline = f"interview {deadline}"
    elif deadline:
        deadline = f"possible deadline {deadline}"
    return EmailHints(category=category, urgency=urgency, deadline_note=deadline)


def summarize_text(provider: LLMProvider, subject: str, body: str) -> str:
    preview = body.strip()[:400]
    fallback = f"{subject}: {preview}" if preview else subject
    if isinstance(provider, FakeProvider):
        return fallback[:500]
    try:
        result = provider.generate(
            [
                ChatMessage(
                    role="system",
                    content=(
                        "Summarize this email in at most 3 short sentences. "
                        "Note any deadline or interview. Do not invent facts."
                    ),
                ),
                ChatMessage(
                    role="user",
                    content=f"Subject: {subject}\n\n{body[:4000]}",
                ),
            ],
            temperature=0.0,
        )
    except LlmError:
        return fallback[:500]
    text = result.text.strip()
    if not text or text.startswith("[fake]"):
        return fallback[:500]
    return text[:1000]


def draft_reply_text(provider: LLMProvider, subject: str, body: str) -> str:
    fallback = (
        f"Thanks for your email about {subject}. I will follow up shortly.\n\n"
        "— Jarvis draft, not sent"
    )
    if isinstance(provider, FakeProvider):
        return fallback
    try:
        result = provider.generate(
            [
                ChatMessage(
                    role="system",
                    content=(
                        "Draft a polite reply. Do not promise it was sent. "
                        "Do not include secrets. Keep it under 120 words."
                    ),
                ),
                ChatMessage(
                    role="user",
                    content=f"Subject: {subject}\n\n{body[:4000]}",
                ),
            ],
            temperature=0.2,
        )
    except LlmError:
        return fallback
    text = result.text.strip()
    if not text or text.startswith("[fake]"):
        return fallback
    return text[:4000]
