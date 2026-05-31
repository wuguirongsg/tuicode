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


# 匹配所有常见终端转义序列：CSI / OSC / G0-G1 字符集 / 单字符 ESC
_ESCAPE_RE = re.compile(
    r"\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)"  # OSC（窗口标题等）
    r"|\x1b\[[0-?]*[ -/]*[@-~]"             # CSI（颜色、光标等）
    r"|\x1b[()][0-9A-Za-z]"                 # G0/G1 字符集指定（如 \x1b(B）
    r"|\x1b[0-9A-Za-z<>=~]"                 # 其他单字符 ESC 序列
)
# 专门提取 OSC 窗口标题（Claude Code 用此携带当前任务描述）
_OSC_TITLE_RE = re.compile(r"\x1b\]0;([^\x07\x1b]+)\x07")
# 清理 OSC 标题开头的 spinner / 状态指示符
_SPINNER_LEAD_RE = re.compile(r"^[\s⠀-⣿⠋-⠏✳✦✶✻⏺⏵⏸●○◉◌⎿►▶]+\s*")

_MAX_TAIL_CHARS = 6000
_IGNORE_LINE_PREFIXES = ("记录了 ", "以下是", "```", "╭", "╰", "│", "─", "❯", "]0;", "(B")
_NOISE_SUBSTRINGS = (
    "shift+tab",
    "bypasspermissions",
    "ClaudeCode",
    "Sonnet",
    "opus",
    "haiku",
    "sourceCode/tuicode",
    "for agents",
    "foragents",
    "←foragents",
    "Tip:Use",
    "Tip: Use",
    "/effort",    # Claude Code effort 指示器（如 ●high·/effort）
    "Seasoning",  # Claude Code 内部状态文本
)


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
    osc_title: str = ""  # Claude Code 通过 OSC 序列设置的当前任务标题


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
    """Remove terminal escape sequences before writing memory files."""
    text = _ESCAPE_RE.sub("", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return "".join(ch for ch in text if ch == "\n" or ch == "\t" or ord(ch) >= 32)


def _extract_osc_title(text: str) -> str:
    """从 PTY 原始字节流中提取最后一个有意义的 OSC 窗口标题。

    Claude Code 通过 OSC 0 设置任务标题（如 "补充项目 README 和开源协议"），
    这是最可靠的会话语义标签来源。
    """
    matches = _OSC_TITLE_RE.findall(text)
    for title in reversed(matches):
        clean = _SPINNER_LEAD_RE.sub("", title).strip()
        if len(clean) >= 4 and clean not in ("Claude Code", "claude"):
            return clean
    return ""


def session_brief(record: AgentSessionRecord, max_len: int = 46) -> str:
    """Return a human-readable description for a saved Agent session."""
    # 最优先：OSC 标题（新会话在 append_output 时实时提取并持久化）
    if record.osc_title:
        return _clip(record.osc_title, max_len)

    # 次优先：从 last_output 中提取 OSC 标题（旧会话的 transcript 未剥离 OSC）
    osc = (_extract_osc_title(record.last_output or "")
           or _extract_osc_title(record.summary or ""))
    if osc:
        return _clip(osc, max_len)

    # 回退：只有匹配到明确任务关键词的行才使用，否则直接返回标题
    candidates = _meaningful_lines(record.summary) + _meaningful_lines(record.last_output)
    preferred = (
        "目标", "需求", "任务", "实现", "修复", "问题", "方案",
        "待办", "TODO", "todo", "fix", "feat",
    )
    for line in candidates:
        if any(token in line for token in preferred):
            return _clip(line, max_len)
    return f"{record.title} 会话"


def session_description(record: AgentSessionRecord, max_len: int = 64) -> str:
    """Return a second-line description for a session card."""
    brief = session_brief(record, max_len=200)
    lines = _display_lines(record.summary, limit=6) + _display_lines(record.last_output, limit=8)
    for line in lines:
        if line != brief:
            return _clip(line, max_len)
    return _clip(f"{record.title} · {record.status}", max_len)


def session_detail(record: AgentSessionRecord, output_chars: int = 1600) -> str:
    """Build a compact detail view for review before continuing."""
    updated = record.updated_at.replace("T", " ")[:19]
    transcript = _short_path(record.transcript_path)
    overview = session_brief(record, max_len=72)
    summary_lines = _display_lines(record.summary, limit=6)
    output_lines = _display_lines(record.last_output[-output_chars:], limit=10)
    return (
        f"{record.title} · {record.agent_type} · {record.status}\n"
        f"更新时间  {updated}\n"
        f"命令      {_clip(record.command, 72)}\n"
        f"Transcript {transcript}\n\n"
        f"概要\n{overview}\n\n"
        f"摘要摘录\n{_format_bullets(summary_lines)}\n\n"
        f"最近关键输出\n{_format_bullets(output_lines)}"
    )


def _meaningful_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw in strip_terminal_output(text).splitlines():
        line = _clean_line(raw)
        if len(line) < 4:
            continue
        if line.startswith(_IGNORE_LINE_PREFIXES):
            continue
        low = line.lower()
        if any(token.lower() in low for token in _NOISE_SUBSTRINGS):
            continue
        if all(ch in "-_=*#~·. " for ch in line):
            continue
        lines.append(line)
    return lines


def _display_lines(text: str, limit: int) -> list[str]:
    seen: set[str] = set()
    lines: list[str] = []
    for line in _meaningful_lines(text):
        clipped = _clip(line, 78)
        if clipped in seen:
            continue
        seen.add(clipped)
        lines.append(clipped)
        if len(lines) >= limit:
            break
    return lines


def _format_bullets(lines: list[str]) -> str:
    if not lines:
        return "  暂无可展示内容"
    return "\n".join(f"  - {line}" for line in lines)


def _clean_line(raw: str) -> str:
    line = re.sub(r"\s+", " ", raw).strip()
    line = line.strip(
        " \t-_=*#~·.▶■●○□▪▫┃│╭╮╰╯━─┏┓┗┛"
        "⏺⏵✳✶✻⎿✦▘▗▖▝"
        "⠁⠂⠃⠄⠅⠆⠇⠈⠉⠊⠋⠌⠍⠎⠏⠐⠑⠒⠓⠔⠕⠖⠗⠘⠙⠚⠛⠜⠝⠞⠟"
        "⠠⠡⠢⠣⠤⠥⠦⠧⠨⠩⠪⠫⠬⠭⠮⠯⠰⠱⠲⠳⠴⠵⠶⠷⠸⠹⠺⠻⠼⠽⠾⠿"
    )
    return line


def _short_path(path: str, max_len: int = 72) -> str:
    if not path:
        return "暂无"
    home = str(Path.home())
    if path.startswith(home):
        path = "~" + path[len(home):]
    return _clip(path, max_len)


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

    def delete_session(self, session_id: str) -> bool:
        """Delete one saved session and its local memory artifacts."""
        records = self._load_records()
        record = records.pop(session_id, None)
        if record is None:
            return False
        for path in (
            Path(record.transcript_path) if record.transcript_path else None,
            self.handoffs_dir / f"{session_id}.md",
        ):
            if path is None:
                continue
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
        self._save_records(records)
        return True

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
        # 在剥离 ESC 前先提取 OSC 标题（strip_terminal_output 会把它删掉）
        osc = _extract_osc_title(text)
        if osc:
            record.osc_title = osc
        clean = strip_terminal_output(text)
        if not clean:
            if osc:
                records[session_id] = record
                self._save_records(records)
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

    def finish_session(
        self,
        session_id: str,
        status: str = "ended",
        scrollback_text: str = "",
    ) -> None:
        records = self._load_records()
        record = records.get(session_id)
        if record is None:
            return
        if not (record.status == "ended" and status == "closed"):
            record.status = status
        record.updated_at = _now_iso()
        if record.transcript_path:
            record.last_output = self._tail(Path(record.transcript_path))
        if scrollback_text.strip():
            record.summary = self._build_pyte_summary(record, scrollback_text)
        elif record.transcript_path:
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

    def _build_pyte_summary(self, record: AgentSessionRecord, scrollback_text: str) -> str:
        """基于 pyte 渲染的干净文本构建摘要（无终端转义乱码）。"""
        osc_hint = f"任务：{record.osc_title}\n" if record.osc_title else ""
        clean_lines = _display_lines(scrollback_text[-12000:], limit=20)
        if not clean_lines:
            return osc_hint + "本轮会话尚未产生可记录内容。"
        content = _format_bullets(clean_lines)
        return f"{osc_hint}会话摘要：\n{content}"

    def _build_summary(self, record: AgentSessionRecord) -> str:
        """从原始 transcript 构建摘要（回退路径，噪声较多）。"""
        osc_hint = f"任务：{record.osc_title}\n" if record.osc_title else ""
        tail = record.last_output.strip()
        if not tail:
            return osc_hint + "本轮会话尚未产生可记录输出。"
        lines = [line.strip() for line in tail.splitlines() if line.strip() and len(line.strip()) > 3]
        snippet = "\n".join(lines[-12:])
        return (
            f"{osc_hint}记录了 {record.title} 的 PTY 会话输出；"
            "以下是最近可观察内容，供后续 agent 接续：\n"
            f"{snippet}"
        )
