"""Shared data types for LLM calls."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


@dataclass(frozen=True)
class GenerateResult:
    text: str
    model: str
    provider: str


@dataclass(frozen=True)
class ClassifyResult:
    label: str
    model: str
    provider: str
    raw_text: str
