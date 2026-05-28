"""Minimal Git status polling service."""
from __future__ import annotations

import subprocess
from pathlib import Path

from tuicode.bus import EventBus, default_bus
from tuicode.events import GitStatusChanged


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
