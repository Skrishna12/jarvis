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
from jarvis.tools.email_tools import (
    EmailClassifyTool,
    EmailDraftTool,
    EmailFetchTool,
    EmailGetTool,
    EmailListTool,
    EmailSearchTool,
    EmailSendTool,
    EmailSummarizeTool,
)
from jarvis.tools.alert_tools import AlertPingTool
from jarvis.tools.briefing_tools import BriefingEveningTool, BriefingMorningTool
from jarvis.tools.calendar_tools import (
    CalendarCreateTool,
    CalendarDeleteTool,
    CalendarListTool,
    CalendarTodayTool,
)
from jarvis.tools.docs_tools import DocsIngestTool, DocsSearchTool
from jarvis.tools.github_tools import GitHubIssuesTool, GitHubPullsTool, GitHubReposTool
from jarvis.tools.commute_tools import (
    CommuteInstallTool,
    CommuteSetCityTool,
    CommuteStatusTool,
    CommuteTrafficTool,
)
from jarvis.tools.news_tools import NewsDigestTool
from jarvis.tools.notify_tools import NotifyListTool, NotifyReadTool
from jarvis.tools.project_tools import ProjectCreateTool, ProjectListTool, ProjectUpdateTool
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
        EmailFetchTool(),
        EmailListTool(),
        EmailGetTool(),
        EmailSearchTool(),
        EmailClassifyTool(),
        EmailSummarizeTool(),
        EmailDraftTool(),
        EmailSendTool(),
        ProjectListTool(),
        ProjectCreateTool(),
        ProjectUpdateTool(),
        CalendarTodayTool(),
        CalendarListTool(),
        CalendarCreateTool(),
        CalendarDeleteTool(),
        GitHubReposTool(),
        GitHubIssuesTool(),
        GitHubPullsTool(),
        DocsIngestTool(),
        DocsSearchTool(),
        NotifyListTool(),
        NotifyReadTool(),
        NewsDigestTool(),
        CommuteStatusTool(),
        CommuteTrafficTool(),
        CommuteSetCityTool(),
        CommuteInstallTool(),
        BriefingMorningTool(),
        BriefingEveningTool(),
        AlertPingTool(),
    ):
        registry.register(tool)
    return registry
