from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Event:
    """所有事件的基类。"""


@dataclass(frozen=True)
class FileOpened(Event):
    path: Path


@dataclass(frozen=True)
class FileModified(Event):
    path: Path
    changes: str = ""  # diff 文本，空字符串表示未知


@dataclass(frozen=True)
class CursorMoved(Event):
    file: Path
    line: int
    col: int


@dataclass(frozen=True)
class SelectionChanged(Event):
    file: Path
    start_line: int
    start_col: int
    end_line: int
    end_col: int
    text: str = ""


@dataclass(frozen=True)
class TerminalOutput(Event):
    session_id: str
    text: str


@dataclass(frozen=True)
class AgentMessage(Event):
    agent_id: str
    content: str
    role: str = "assistant"  # "assistant" | "user" | "tool"


@dataclass(frozen=True)
class ToolCallRequested(Event):
    agent_id: str
    tool: str
    args: dict[str, Any] = field(default_factory=dict)
    call_id: str = ""


@dataclass(frozen=True)
class GitStatusChanged(Event):
    changed_files: tuple[str, ...] = field(default_factory=tuple)
    branch: str = ""
    ahead: int = 0
    behind: int = 0
