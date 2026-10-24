from __future__ import annotations

from jarvis.security.errors import ToolNotFoundError
from jarvis.tools.base import Tool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        tool = self._tools.get(name)
        if tool is None:
            known = ", ".join(sorted(self._tools)) or "(none)"
            raise ToolNotFoundError(
                f"Unknown tool {name!r}. Available tools: {known}."
            )
        return tool

    def all(self) -> list[Tool]:
        return [self._tools[name] for name in sorted(self._tools)]
