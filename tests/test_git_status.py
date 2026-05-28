"""feat-012 单元测试 — Git 状态轮询。"""
from __future__ import annotations

import subprocess
from pathlib import Path

from tuicode.bus import EventBus
from tuicode.events import GitStatusChanged
from tuicode.git_status import GitStatusPoller


def _git(root: Path, *args: str) -> None:
    subprocess.run(("git", "-C", str(root), *args), check=True, capture_output=True)


def test_git_status_poller_publishes_status_short(tmp_path: Path):
    _git(tmp_path, "init")
    target = tmp_path / "main.py"
    target.write_text("x = 1", encoding="utf-8")
    bus = EventBus()
    received: list[GitStatusChanged] = []
    bus.subscribe(GitStatusChanged, received.append)
    poller = GitStatusPoller(tmp_path, bus=bus)

    event = poller.poll()

    assert event is not None
    assert received == [event]
    assert event.branch
    assert event.changed_files == ("?? main.py",)


def test_git_status_poller_skips_unchanged_status(tmp_path: Path):
    _git(tmp_path, "init")
    bus = EventBus()
    received: list[GitStatusChanged] = []
    bus.subscribe(GitStatusChanged, received.append)
    poller = GitStatusPoller(tmp_path, bus=bus)

    first = poller.poll()
    second = poller.poll()

    assert first is not None
    assert second is None
    assert received == [first]
