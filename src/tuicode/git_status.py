"""Minimal Git status polling service + single-file git operations."""
from __future__ import annotations

import subprocess
from pathlib import Path

from tuicode.bus import EventBus, default_bus
from tuicode.events import GitStatusChanged


class GitError(Exception):
    """Raised when a git operation fails."""


class GitOps:
    """Thin wrapper for per-file git operations used by the Git panel."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root).resolve()

    def stage(self, rel_path: str) -> None:
        """Stage a file (git add)."""
        self._run("add", "--", rel_path)

    def unstage(self, rel_path: str) -> None:
        """Unstage a file.

        Before the first commit HEAD does not exist, so git restore --staged
        would fail. In that case fall back to git rm --cached which correctly
        returns a newly-added file to untracked state.
        """
        if self._head_exists():
            self._run("restore", "--staged", "--", rel_path)
        else:
            self._run("rm", "--cached", "--", rel_path)

    def _head_exists(self) -> bool:
        try:
            result = subprocess.run(
                ("git", "-C", str(self.root), "rev-parse", "--verify", "HEAD"),
                check=False,
                capture_output=True,
                text=True,
                timeout=2.0,
            )
            return result.returncode == 0
        except (OSError, subprocess.SubprocessError):
            return False

    def commit(self, message: str) -> None:
        """Create a commit with the given message."""
        if not message.strip():
            raise GitError("commit message cannot be empty")
        self._run("commit", "-m", message)

    def _run(self, *args: str) -> None:
        try:
            result = subprocess.run(
                ("git", "-C", str(self.root), *args),
                check=False,
                capture_output=True,
                text=True,
                timeout=10.0,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise GitError(str(exc)) from exc
        if result.returncode != 0:
            raise GitError(result.stderr.strip() or result.stdout.strip() or "git error")


class GitStatusPoller:
    """Poll git status and publish GitStatusChanged when it changes."""

    def __init__(self, root: Path | str, *, bus: EventBus = default_bus) -> None:
        self.root = Path(root).resolve()
        self._bus = bus
        self._last_key: tuple[str, tuple[str, ...]] | None = None

    def poll(self) -> GitStatusChanged | None:
        branch = self._git("branch", "--show-current")
        status = self._git("status", "--short")
        if branch is None or status is None:
            return None

        lines = tuple(line for line in status.splitlines() if line)
        key = (branch, lines)
        if key == self._last_key:
            return None
        self._last_key = key

        event = GitStatusChanged(changed_files=lines, branch=branch)
        self._bus.publish(event)
        return event

    def _git(self, *args: str) -> str | None:
        try:
            result = subprocess.run(
                ("git", "-C", str(self.root), *args),
                check=False,
                capture_output=True,
                text=True,
                timeout=2.0,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if result.returncode != 0:
            return None
        return result.stdout.strip()
