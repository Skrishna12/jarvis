"""`jarvis llm` — call generate / stream / classify through the provider interface."""

from __future__ import annotations

import argparse
import sys

from jarvis.config import load_settings
from jarvis.llm.errors import LlmError
from jarvis.llm.factory import build_provider
from jarvis.llm.types import ChatMessage


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "llm",
        help="Call the configured LLM provider (no agents yet).",
    )
    sub = parser.add_subparsers(dest="llm_command", required=True)

    gen = sub.add_parser("generate", help="One-shot completion.")
    gen.add_argument("prompt")
    gen.add_argument("--system", default="")
    gen.set_defaults(handler=cmd_generate)

    stream = sub.add_parser("stream", help="Print tokens as they arrive.")
    stream.add_argument("prompt")
    stream.add_argument("--system", default="")
    stream.set_defaults(handler=cmd_stream)

    classify = sub.add_parser("classify", help="Pick one label for the text.")
    classify.add_argument("text")
    classify.add_argument(
        "--labels",
        required=True,
        help="Comma-separated labels, e.g. TASK,REMINDER,CHAT",
    )
    classify.set_defaults(handler=cmd_classify)


def _messages(prompt: str, system: str) -> list[ChatMessage]:
    messages: list[ChatMessage] = []
    if system.strip():
        messages.append(ChatMessage(role="system", content=system))
    messages.append(ChatMessage(role="user", content=prompt))
    return messages


def _provider():
    return build_provider(load_settings())


def cmd_generate(args: argparse.Namespace) -> int:
    try:
        result = _provider().generate(_messages(args.prompt, args.system))
    except LlmError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(result.text)
    return 0


def cmd_stream(args: argparse.Namespace) -> int:
    try:
        for chunk in _provider().stream(_messages(args.prompt, args.system)):
            print(chunk, end="", flush=True)
        print()
    except LlmError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


def cmd_classify(args: argparse.Namespace) -> int:
    labels = [part.strip() for part in args.labels.split(",")]
    try:
        result = _provider().classify(args.text, labels)
    except LlmError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(result.label)
    return 0
