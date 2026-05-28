"""feat-010 单元测试 — 工作区文件变化感知。"""
from __future__ import annotations

import time
from pathlib import Path

from tuicode.bus import EventBus
from tuicode.events import FileModified
from tuicode.workspace_watcher import WorkspaceWatcher


def test_watcher_publishes_modified_file(tmp_path: Path):
    target = tmp_path / "main.py"
    target.write_text("old", encoding="utf-8")
    bus = EventBus()
    received: list[FileModified] = []
    bus.subscribe(FileModified, received.append)
    watcher = WorkspaceWatcher(tmp_path, bus=bus)

    time.sleep(0.001)
    target.write_text("new content", encoding="utf-8")

    changed = watcher.poll()

    assert target.resolve() in changed
    assert [event.path for event in received] == [target.resolve()]


def test_watcher_publishes_created_file(tmp_path: Path):
    bus = EventBus()
    received: list[FileModified] = []
    bus.subscribe(FileModified, received.append)
    watcher = WorkspaceWatcher(tmp_path, bus=bus)
    target = tmp_path / "created.py"

    target.write_text("x = 1", encoding="utf-8")

    changed = watcher.poll()

    assert target.resolve() in changed
    assert [event.path for event in received] == [target.resolve()]


def test_watcher_publishes_deleted_file(tmp_path: Path):
    target = tmp_path / "deleted.py"
    target.write_text("x = 1", encoding="utf-8")
    bus = EventBus()
    received: list[FileModified] = []
    bus.subscribe(FileModified, received.append)
    watcher = WorkspaceWatcher(tmp_path, bus=bus)

    target.unlink()

    changed = watcher.poll()

    assert target.resolve() in changed
    assert [event.path for event in received] == [target.resolve()]
