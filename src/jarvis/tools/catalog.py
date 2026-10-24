"""Default tools the orchestrator and CLI may call."""

from __future__ import annotations

from jarvis.tools.memory_tools import (
    MemoryDeleteTool,
    MemoryGetTool,
    MemoryListTool,
    MemoryUpsertTool,
)
from jarvis.tools.registry import ToolRegistry
from jarvis.tools.reminder_tools import (
    ReminderCreateTool,
    ReminderDeleteTool,
    ReminderDueTool,
    ReminderListTool,
)
from jarvis.tools.task_tools import (
    TaskAddSubtaskTool,
    TaskCompleteTool,
    TaskCreateTool,
    TaskDeleteTool,
    TaskGetTool,
    TaskListTool,
    TaskPrioritizeTool,
    TaskUpdateTool,
)


def default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    for tool in (
        MemoryGetTool(),
        MemoryListTool(),
        MemoryUpsertTool(),
        MemoryDeleteTool(),
        TaskListTool(),
        TaskGetTool(),
        TaskCreateTool(),
        TaskUpdateTool(),
        TaskCompleteTool(),
        TaskPrioritizeTool(),
        TaskAddSubtaskTool(),
        TaskDeleteTool(),
        ReminderListTool(),
        ReminderDueTool(),
        ReminderCreateTool(),
        ReminderDeleteTool(),
    ):
        registry.register(tool)
    return registry
