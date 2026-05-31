"""系统剪贴板读写工具，支持 macOS (pbcopy/pbpaste) 和 Linux (wl-copy/xclip/xsel)。"""
from __future__ import annotations

import subprocess


def _run(cmd: list[str], *, stdin_text: str | None = None, timeout: float = 1.0) -> str | None:
    try:
        result = subprocess.run(
            cmd,
            input=stdin_text,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.stdout if result.returncode == 0 else None
    except (FileNotFoundError, subprocess.TimeoutExpired, PermissionError, OSError):
        return None


def read() -> str:
    """从系统剪贴板读取文本，所有途径失败时返回空字符串。"""
    for cmd in [
        ["pbpaste"],
        ["wl-paste", "--no-newline"],
        ["xclip", "-selection", "clipboard", "-o"],
        ["xsel", "--clipboard", "--output"],
    ]:
        text = _run(cmd)
        if text is not None:
            return text
    return ""


def write(text: str) -> None:
    """将文本写入系统剪贴板，所有途径失败时静默忽略。"""
    for cmd in [
        ["pbcopy"],
        ["wl-copy"],
        ["xclip", "-selection", "clipboard"],
        ["xsel", "--clipboard", "--input"],
    ]:
        if _run(cmd, stdin_text=text) is not None:
            return
