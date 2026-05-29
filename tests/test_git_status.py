"""feat-012/feat-015 单元测试 — Git 状态轮询 + GitOps 操作。"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tuicode.bus import EventBus
from tuicode.events import GitStatusChanged
from tuicode.git_status import GitError, GitOps, GitStatusPoller


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


# ── GitOps ─────────────────────────────────────────────────────────────────


def _setup_repo(root: Path) -> None:
    _git(root, "init")
    _git(root, "config", "user.email", "test@test.com")
    _git(root, "config", "user.name", "Test")


def test_git_ops_stage_untracked_file(tmp_path: Path):
    _setup_repo(tmp_path)
    (tmp_path / "a.txt").write_text("hello", encoding="utf-8")
    ops = GitOps(tmp_path)

    ops.stage("a.txt")

    result = subprocess.run(
        ("git", "-C", str(tmp_path), "status", "--short"),
        capture_output=True, text=True, check=True,
    )
    assert result.stdout.strip().startswith("A")


def test_git_ops_unstage_staged_file(tmp_path: Path):
    _setup_repo(tmp_path)
    (tmp_path / "a.txt").write_text("hello", encoding="utf-8")
    ops = GitOps(tmp_path)
    ops.stage("a.txt")

    ops.unstage("a.txt")

    result = subprocess.run(
        ("git", "-C", str(tmp_path), "status", "--short"),
        capture_output=True, text=True, check=True,
    )
    assert result.stdout.strip().startswith("??")


def test_git_ops_commit_success(tmp_path: Path):
    _setup_repo(tmp_path)
    (tmp_path / "a.txt").write_text("hello", encoding="utf-8")
    ops = GitOps(tmp_path)
    ops.stage("a.txt")

    ops.commit("initial commit")

    result = subprocess.run(
        ("git", "-C", str(tmp_path), "log", "--oneline"),
        capture_output=True, text=True, check=True,
    )
    assert "initial commit" in result.stdout


def test_git_ops_commit_empty_message_raises(tmp_path: Path):
    _setup_repo(tmp_path)
    (tmp_path / "a.txt").write_text("hello", encoding="utf-8")
    ops = GitOps(tmp_path)
    ops.stage("a.txt")

    with pytest.raises(GitError, match="empty"):
        ops.commit("   ")


def test_git_ops_commit_nothing_staged_raises(tmp_path: Path):
    _setup_repo(tmp_path)
    ops = GitOps(tmp_path)

    with pytest.raises(GitError):
        ops.commit("no staged files")
