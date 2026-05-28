"""feat-014 单元测试 — Git diff 只读预览数据源。"""
from __future__ import annotations

import subprocess
from pathlib import Path

from tuicode.git_diff import GitDiffService


def _git(root: Path, *args: str) -> None:
    subprocess.run(("git", "-C", str(root), *args), check=True, capture_output=True)


def test_file_diff_reads_modified_worktree_file(tmp_path: Path):
    _git(tmp_path, "init")
    target = tmp_path / "main.py"
    target.write_text("keep = 1\nold = True\ntail = 2\n", encoding="utf-8")
    _git(tmp_path, "add", "main.py")
    target.write_text("keep = 1\nnew = True\ntail = 2\n", encoding="utf-8")

    diff = GitDiffService(tmp_path).file_diff(target)

    assert "-old = True" in diff
    assert "+new = True" in diff
    assert " keep = 1" in diff
    assert "diff --git" in diff


def test_file_diff_reads_untracked_file(tmp_path: Path):
    _git(tmp_path, "init")
    target = tmp_path / "created.py"
    target.write_text("x = 1\n", encoding="utf-8")

    diff = GitDiffService(tmp_path).file_diff(target)

    assert "+x = 1" in diff
    assert "/dev/null" in diff
