"""Workspace file change watcher for external edits."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from tuicode.bus import EventBus, default_bus
from tuicode.events import FileModified


_IGNORED_DIRS = {
    # VCS
    ".git", ".hg", ".svn",
    # Python
    ".venv", "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    ".tox", ".eggs", "dist", "build",
    # JS / Node
    "node_modules", ".next", ".nuxt", ".angular",
    # Rust / Java / others
    "target", ".gradle", "out", "coverage",
}


@dataclass(frozen=True)
class FileSignature:
    """Compact file identity used to detect changes."""

    mtime_ns: int
    size: int


class WorkspaceWatcher:
    """Poll the workspace and publish FileModified for changed files."""

    def __init__(
        self,
        root: Path | str,
        *,
        bus: EventBus = default_bus,
        ignored_dirs: set[str] | None = None,
    ) -> None:
        self.root = Path(root).resolve()
        self._bus = bus
        self._ignored_dirs = _IGNORED_DIRS | (ignored_dirs or set())
        self._snapshot = self._scan()

    def poll(self) -> list[Path]:
        """Scan once and publish events for added, modified, or deleted files."""
        current = self._scan()
        changed: list[Path] = []

        for path, signature in current.items():
            if self._snapshot.get(path) != signature:
                changed.append(path)

        for path in self._snapshot:
            if path not in current:
                changed.append(path)

        self._snapshot = current

        for path in changed:
            self._bus.publish(FileModified(path))

        return changed

    def _scan(self) -> dict[Path, FileSignature]:
        files: dict[Path, FileSignature] = {}
        if not self.root.exists():
            return files

        for dirpath, dirnames, filenames in os.walk(self.root):
            # Prune ignored dirs in-place: os.walk won't descend into them
            dirnames[:] = [d for d in dirnames if d not in self._ignored_dirs]
            for filename in filenames:
                full_path = Path(dirpath) / filename
                try:
                    stat = full_path.stat()
                except OSError:
                    continue
                files[full_path.resolve()] = FileSignature(
                    mtime_ns=stat.st_mtime_ns,
                    size=stat.st_size,
                )
        return files
