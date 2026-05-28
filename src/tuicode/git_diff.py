"""Git diff helpers for read-only previews."""
from __future__ import annotations

import subprocess
from pathlib import Path


class GitDiffService:
    """Read file-level diffs without mutating the working tree or index."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root).resolve()

    def file_diff(self, path: Path | str) -> str:
        target = Path(path)
        if not target.is_absolute():
            target = self.root / target
        try:
            rel = target.resolve().relative_to(self.root)
        except ValueError:
            return ""

        status = self._git("status", "--short", "--", str(rel))
        if status is not None and status.startswith("??"):
            return self._no_index_diff(target)

        diff = self._git("diff", "--", str(rel))
        if diff:
            return diff
        return self._git("diff", "--cached", "--", str(rel)) or ""

    def _no_index_diff(self, target: Path) -> str:
        result = self._run(("diff", "--no-index", "--", "/dev/null", str(target)))
        return result or ""

    def _git(self, *args: str) -> str | None:
        return self._run(args)

    def _run(self, args: tuple[str, ...]) -> str | None:
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
        if result.returncode not in (0, 1):
            return None
        return result.stdout
