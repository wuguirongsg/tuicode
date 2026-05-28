"""Workspace state aggregation backed by the event bus."""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from tuicode.agent_protocol import Context
from tuicode.bus import EventBus, default_bus
from tuicode.events import FileModified, FileOpened, GitStatusChanged, SelectionChanged


class WorkspaceStateAggregator:
    """Maintain a compact synchronous context snapshot for the workspace."""

    def __init__(self, *, bus: EventBus = default_bus, max_recent_changes: int = 10) -> None:
        self._bus = bus
        self._max_recent_changes = max_recent_changes
        self.active_file: Path | None = None
        self.selection_text = ""
        self.recent_changes: list[str] = []
        self.git_status = ""
        self._unsubscribers: list[Callable[[], None]] = [
            bus.subscribe(FileOpened, self._on_file_opened),
            bus.subscribe(SelectionChanged, self._on_selection_changed),
            bus.subscribe(FileModified, self._on_file_modified),
            bus.subscribe(GitStatusChanged, self._on_git_status_changed),
        ]

    def close(self) -> None:
        for unsubscribe in self._unsubscribers:
            unsubscribe()
        self._unsubscribers.clear()

    def get_context(self) -> Context:
        return Context(
            active_file=self.active_file,
            selection_text=self.selection_text,
            git_status=self.git_status,
            recent_diffs=list(self.recent_changes),
        )

    def _on_file_opened(self, event: FileOpened) -> None:
        self.active_file = event.path

    def _on_selection_changed(self, event: SelectionChanged) -> None:
        self.active_file = event.file
        self.selection_text = event.text

    def _on_file_modified(self, event: FileModified) -> None:
        summary = str(event.path)
        if event.changes:
            summary = f"{summary}: {event.changes}"
        self.recent_changes.append(summary)
        del self.recent_changes[:-self._max_recent_changes]

    def _on_git_status_changed(self, event: GitStatusChanged) -> None:
        parts: list[str] = []
        if event.branch:
            parts.append(event.branch)
        if event.changed_files:
            parts.append(f"{len(event.changed_files)} changed")
            parts.append(", ".join(event.changed_files[:5]))
        if event.ahead or event.behind:
            parts.append(f"ahead {event.ahead} behind {event.behind}")
        self.git_status = " | ".join(parts)
