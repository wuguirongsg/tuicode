"""feat-011 单元测试 — 工作区状态聚合器。"""
from __future__ import annotations

from pathlib import Path

from tuicode.bus import EventBus
from tuicode.events import FileModified, FileOpened, GitStatusChanged, SelectionChanged
from tuicode.workspace_state import WorkspaceStateAggregator


def test_get_context_returns_active_file_selection_and_git_status(tmp_path: Path):
    bus = EventBus()
    aggregator = WorkspaceStateAggregator(bus=bus)
    target = tmp_path / "main.py"

    bus.publish(FileOpened(target))
    bus.publish(
        SelectionChanged(
            file=target,
            start_line=1,
            start_col=0,
            end_line=1,
            end_col=5,
            text="hello",
        )
    )
    bus.publish(FileModified(target, changes="modified"))
    bus.publish(GitStatusChanged(branch="main", changed_files=("main.py",)))

    ctx = aggregator.get_context()

    assert ctx.active_file == target
    assert ctx.selection_text == "hello"
    assert ctx.recent_diffs == [f"{target}: modified"]
    assert ctx.git_status == "main | 1 changed | main.py"


def test_recent_changes_keeps_last_ten(tmp_path: Path):
    bus = EventBus()
    aggregator = WorkspaceStateAggregator(bus=bus)

    for i in range(12):
        bus.publish(FileModified(tmp_path / f"{i}.py"))

    ctx = aggregator.get_context()

    assert len(ctx.recent_diffs) == 10
    assert ctx.recent_diffs[0].endswith("2.py")
    assert ctx.recent_diffs[-1].endswith("11.py")


def test_close_unsubscribes_from_bus(tmp_path: Path):
    bus = EventBus()
    aggregator = WorkspaceStateAggregator(bus=bus)
    target = tmp_path / "main.py"

    aggregator.close()
    bus.publish(FileOpened(target))

    assert aggregator.get_context().active_file is None
