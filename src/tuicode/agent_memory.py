"""Project-scoped Agent session memory.

This is deliberately agent-agnostic: it stores what TuiCode can observe from
PTY sessions, then builds a continuation prompt that any later agent can use.
It does not try to restore a provider's private native conversation state.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha1
from pathlib import Path
import json
import os
import re


_ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_MAX_TAIL_CHARS = 6000
_IGNORE_LINE_PREFIXES = ("记录了 ", "以下是", "```", "╭", "╰", "│", "─")


@dataclass
class AgentSessionRecord:
    session_id: str
    project_root: str
    title: str
    agent_type: str
    command: str
    created_at: str
    updated_at: str
    status: str = "running"
    transcript_path: str = ""
    summary: str = ""
    last_output: str = ""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _default_data_home() -> Path:
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg)
    return Path.home() / ".local" / "share"


def _project_key(root: Path) -> str:
    resolved = str(root.resolve())
    return sha1(resolved.encode("utf-8")).hexdigest()[:16]


def strip_terminal_output(text: str) -> str:
    """Remove common terminal control sequences before writing memory files."""
    text = _ANSI_RE.sub("", text)
    return text.replace("\r\n", "\n").replace("\r", "\n")


def session_brief(record: AgentSessionRecord, max_len: int = 46) -> str:
    """Return a human-readable description for a saved Agent session."""
    candidates = _meaningful_lines(record.summary) + _meaningful_lines(record.last_output)
    if not candidates:
        return "暂无摘要"

    preferred = (
        "目标", "需求", "任务", "实现", "修复", "问题", "方案",
        "待办", "TODO", "todo", "fix", "feat",
    )
    for line in candidates:
        if any(token in line for token in preferred):
            return _clip(line, max_len)
    return _clip(candidates[0], max_len)


def session_detail(record: AgentSessionRecord, output_chars: int = 1600) -> str:
    """Build a compact detail view for review before continuing."""
    summary = record.summary.strip() or "暂无自动摘要"
    tail = record.last_output.strip()[-output_chars:] or "暂无最近输出"
    return (
        f"会话：{record.title} ({record.agent_type})\n"
        f"状态：{record.status}\n"
        f"更新时间：{record.updated_at}\n"
        f"命令：{record.command}\n"
        f"Transcript：{record.transcript_path or '暂无'}\n\n"
        f"摘要：\n{summary}\n\n"
        f"最近输出：\n{tail}"
    )


def _meaningful_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw in strip_terminal_output(text).splitlines():
        line = re.sub(r"\s+", " ", raw).strip()
        if len(line) < 4:
            continue
        if line.startswith(_IGNORE_LINE_PREFIXES):
            continue
        if all(ch in "-_=*#~·. " for ch in line):
            continue
        lines.append(line)
    return lines


def _clip(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


class AgentSessionStore:
    """Persistent store for one project's observed Agent sessions."""

    def __init__(self, project_root: Path | str = ".", data_home: Path | None = None) -> None:
        self.project_root = Path(project_root).resolve()
        base = data_home or _default_data_home()
        self.root = base / "tuicode" / "projects" / _project_key(self.project_root)
        self.transcripts_dir = self.root / "transcripts"
        self.handoffs_dir = self.root / "handoffs"
        self.index_path = self.root / "agent_sessions.json"
        self.root.mkdir(parents=True, exist_ok=True)
        self.transcripts_dir.mkdir(parents=True, exist_ok=True)
        self.handoffs_dir.mkdir(parents=True, exist_ok=True)

    def list_sessions(self, limit: int | None = None) -> list[AgentSessionRecord]:
        records = sorted(
            self._load_records().values(),
            key=lambda r: r.updated_at,
            reverse=True,
        )
        return records if limit is None else records[:limit]

    def get(self, session_id: str) -> AgentSessionRecord | None:
        return self._load_records().get(session_id)

    def start_session(
        self,
        *,
        session_id: str,
        title: str,
        agent_type: str,
        command: str,
    ) -> AgentSessionRecord:
        records = self._load_records()
        now = _now_iso()
        transcript = self.transcripts_dir / f"{session_id}.txt"
        record = AgentSessionRecord(
            session_id=session_id,
            project_root=str(self.project_root),
            title=title,
            agent_type=agent_type,
            command=command,
            created_at=now,
            updated_at=now,
            transcript_path=str(transcript),
        )
        records[session_id] = record
        self._save_records(records)
        transcript.touch(exist_ok=True)
        return record

    def append_output(self, session_id: str, text: str) -> None:
        if not text:
            return
        records = self._load_records()
        record = records.get(session_id)
        if record is None:
            return
        clean = strip_terminal_output(text)
        if not clean:
            return
        transcript = Path(record.transcript_path)
        transcript.parent.mkdir(parents=True, exist_ok=True)
        with transcript.open("a", encoding="utf-8") as fh:
            fh.write(clean)
        record.updated_at = _now_iso()
        record.last_output = self._tail(transcript)
        record.summary = self._build_summary(record)
        records[session_id] = record
        self._save_records(records)

    def finish_session(self, session_id: str, status: str = "ended") -> None:
        records = self._load_records()
        record = records.get(session_id)
        if record is None:
            return
        if not (record.status == "ended" and status == "closed"):
            record.status = status
        record.updated_at = _now_iso()
        if record.transcript_path:
            record.last_output = self._tail(Path(record.transcript_path))
            record.summary = self._build_summary(record)
        records[session_id] = record
        self._save_records(records)

    def build_continuation_prompt(self, session_id: str) -> str:
        record = self.get(session_id)
        if record is None:
            return ""
        tail = record.last_output or self._tail(Path(record.transcript_path))
        tail = tail[-_MAX_TAIL_CHARS:]
        return (
            "请继续这个 TuiCode 项目的上一轮 agent 会话。\n\n"
            f"上一轮 agent: {record.title} ({record.agent_type})\n"
            f"上一轮命令: {record.command}\n"
            f"上一轮 session_id: {record.session_id}\n"
            f"项目目录: {record.project_root}\n"
            f"结束状态: {record.status}\n"
            f"更新时间: {record.updated_at}\n\n"
            "上一轮会话摘要:\n"
            f"{record.summary or '暂无自动摘要'}\n\n"
            "最近 transcript 片段:\n"
            "```text\n"
            f"{tail.strip() or '暂无 transcript'}\n"
            "```\n\n"
            "请先检查当前工作区和 Git 状态，再基于以上上下文继续。"
        )

    def write_continuation_handoff(self, session_id: str) -> Path | None:
        """Write the full continuation context to a markdown handoff file."""
        prompt = self.build_continuation_prompt(session_id)
        if not prompt:
            return None
        path = self.handoffs_dir / f"{session_id}.md"
        path.write_text(prompt + "\n", encoding="utf-8")
        return path

    def build_handoff_notice(self, session_id: str) -> str:
        """Build a short one-line prompt that points an agent at the handoff file."""
        path = self.write_continuation_handoff(session_id)
        if path is None:
            return ""
        return (
            "请继续上一轮 TuiCode agent 会话。"
            f"完整上下文已保存到 {path}，请先读取该文件，"
            "再检查当前工作区和 Git 状态后继续。"
        )

    def _load_records(self) -> dict[str, AgentSessionRecord]:
        if not self.index_path.exists():
            return {}
        try:
            raw = json.loads(self.index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        records: dict[str, AgentSessionRecord] = {}
        for item in raw.get("sessions", []):
            try:
                record = AgentSessionRecord(**item)
            except TypeError:
                continue
            records[record.session_id] = record
        return records

    def _save_records(self, records: dict[str, AgentSessionRecord]) -> None:
        data = {
            "project_root": str(self.project_root),
            "sessions": [asdict(r) for r in records.values()],
        }
        self.index_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _tail(self, path: Path, max_chars: int = _MAX_TAIL_CHARS) -> str:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""
        return text[-max_chars:]

    def _build_summary(self, record: AgentSessionRecord) -> str:
        tail = record.last_output.strip()
        if not tail:
            return "本轮会话尚未产生可记录输出。"
        lines = [line.strip() for line in tail.splitlines() if line.strip()]
        snippet = "\n".join(lines[-12:])
        return (
            f"记录了 {record.title} 的 PTY 会话输出；"
            "以下是最近可观察内容，供后续 agent 接续：\n"
            f"{snippet}"
        )
