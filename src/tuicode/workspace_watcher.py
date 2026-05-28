"""Workspace file change watcher for external edits."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tuicode.bus import EventBus, default_bus
from tuicode.events import FileModified


_IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "node_modules",
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

        for path in self.root.rglob("*"):
            if self._is_ignored(path) or not path.is_file():
                continue
            try:
                stat = path.stat()
            except OSError:
                continue
            files[path.resolve()] = FileSignature(
                mtime_ns=stat.st_mtime_ns,
                size=stat.st_size,
            )
        return files

    def _is_ignored(self, path: Path) -> bool:
        try:
            relative = path.relative_to(self.root)
        except ValueError:
            return True
        return any(part in self._ignored_dirs for part in relative.parts)
