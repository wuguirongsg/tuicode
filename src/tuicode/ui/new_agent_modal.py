"""feat-017 新建 Agent 启动器 — ModalScreen 选择 Agent 类型。"""
from __future__ import annotations

from dataclasses import dataclass

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Button, Input, Label


@dataclass
class AgentConfig:
    """用户在启动器中选择/输入的会话配置。"""
    command: str
    title: str
    agent_type: str


_PRESETS: list[tuple[str, str, str]] = [
    # (显示名称, 启动命令, agent_type)
    # ── 国际主流 ──────────────────────────────────────────
    ("Claude Code",  "claude --dangerously-skip-permissions", "claude"),
    ("Codex",        "codex",    "codex"),
    ("OpenCode",     "opencode", "opencode"),
    ("OMP",          "omp",      "omp"),
    ("Crush",        "crush",    "crush"),
    ("Hermes",       "hermes",   "hermes"),
    ("Aider",        "aider",    "aider"),
    ("Gemini",       "gemini",   "gemini"),
    ("Goose",        "goose",    "goose"),
    # ── 国内 ─────────────────────────────────────────────
    ("通义灵码",      "lingma",   "lingma"),
    ("Kimi",         "kimi",     "kimi"),
    # ── 通用备选 ─────────────────────────────────────────
    ("Bash",         "/bin/bash", "bash"),
]


class NewAgentModal(ModalScreen[AgentConfig | None]):
    """全屏 Modal — 选择 Agent 类型或输入自定义命令，返回 AgentConfig。

    Dismiss with None 表示用户取消（Escape）。
    """

    DEFAULT_CSS = """
    NewAgentModal {
        align: center middle;
    }
    NewAgentModal #modal-box {
        width: 56;
        height: 90vh;
        border: round $accent;
        background: $surface;
        padding: 1 2;
    }
    NewAgentModal #preset-scroll {
        height: 1fr;
        overflow-y: auto;
    }
    NewAgentModal #modal-title {
        width: 1fr;
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    NewAgentModal .preset-btn {
        width: 1fr;
        margin-bottom: 0;
    }
    NewAgentModal #custom-label {
        margin-top: 1;
        color: $text-muted;
    }
    NewAgentModal #custom-input {
        width: 1fr;
        margin-top: 0;
    }
    NewAgentModal #btn-row {
        layout: horizontal;
        height: auto;
        margin-top: 1;
    }
    NewAgentModal #btn-ok {
        width: 1fr;
    }
    NewAgentModal #btn-cancel {
        width: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        with Widget(id="modal-box"):
            yield Label("新建 Agent 会话", id="modal-title")
            with VerticalScroll(id="preset-scroll"):
                for label, cmd, atype in _PRESETS:
                    yield Button(label, id=f"preset-{atype}", classes="preset-btn", variant="default")
            yield Label("自定义命令：", id="custom-label")
            yield Input(placeholder="e.g. opencode / python agent.py", id="custom-input")
            with Widget(id="btn-row"):
                yield Button("启动", id="btn-ok", variant="success")
                yield Button("取消", id="btn-cancel", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        btn_id = event.button.id

        if btn_id == "btn-cancel":
            self.dismiss(None)
            return

        if btn_id == "btn-ok":
            cmd = self.query_one("#custom-input", Input).value.strip()
            if cmd:
                self.dismiss(AgentConfig(command=cmd, title="Custom", agent_type="custom"))
            return

        for label, cmd, atype in _PRESETS:
            if btn_id == f"preset-{atype}":
                self.dismiss(AgentConfig(command=cmd, title=label, agent_type=atype))
                return

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)
            event.stop()
