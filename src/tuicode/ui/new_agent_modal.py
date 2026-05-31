"""feat-017 新建 Agent 启动器 — ModalScreen 选择 Agent 类型。"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shlex
import shutil
from collections.abc import Callable

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual import events
from textual.message import Message
from textual.screen import ModalScreen
from textual.strip import Strip
from textual.widget import Widget
from textual.widgets import Button, Input, Label

from rich.cells import cell_len, set_cell_size
from rich.segment import Segment
from rich.style import Style

from tuicode.i18n import t


@dataclass
class AgentConfig:
    """用户在启动器中选择/输入的会话配置。"""
    command: str
    title: str
    agent_type: str


@dataclass(frozen=True)
class AgentOption:
    """An agent candidate that can be selected in the launcher grid."""

    label: str
    command: str
    agent_type: str
    source: str = "detected"


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
    ("Qwen Code",    "qwen",     "qwen"),
    ("Amazon Q",     "q",        "amazon-q"),
    ("Amp",          "amp",      "amp"),
    ("Cursor Agent", "cursor-agent", "cursor-agent"),
    ("Cody",         "cody",     "cody"),
    ("OpenHands",    "openhands", "openhands"),
    # ── 国内 ─────────────────────────────────────────────
    ("通义灵码",      "lingma",   "lingma"),
    ("Kimi",         "kimi",     "kimi"),
    # ── 通用备选 ─────────────────────────────────────────
    ("Bash",         "/bin/bash", "bash"),
]


_EXECUTABLE_ALIASES: dict[str, tuple[str, ...]] = {
    "claude": ("claude", "claude-code"),
    "codex": ("codex",),
    "opencode": ("opencode", "open-code"),
    "omp": ("omp",),
    "crush": ("crush",),
    "hermes": ("hermes",),
    "aider": ("aider",),
    "gemini": ("gemini",),
    "goose": ("goose",),
    "qwen": ("qwen", "qwen-code"),
    "amazon-q": ("q",),
    "amp": ("amp",),
    "cursor-agent": ("cursor-agent",),
    "cody": ("cody",),
    "openhands": ("openhands", "openhands-cli"),
    "lingma": ("lingma", "lingma-agent"),
    "kimi": ("kimi",),
    "bash": ("/bin/bash", "bash"),
}


def _command_executable(command: str) -> str:
    try:
        return shlex.split(command)[0]
    except (IndexError, ValueError):
        return command.strip().split(maxsplit=1)[0] if command.strip() else ""


def _is_installed(executable: str) -> bool:
    if not executable:
        return False
    if "/" in executable:
        return Path(executable).exists()
    return shutil.which(executable) is not None


def detect_installed_agents() -> list[AgentOption]:
    """Return known agent CLIs that are installed locally.

    Detection is intentionally passive: it checks executable presence only and
    never starts the candidate command.
    """

    detected: list[AgentOption] = []
    for label, command, agent_type in _PRESETS:
        aliases = _EXECUTABLE_ALIASES.get(
            agent_type,
            (_command_executable(command),),
        )
        if any(_is_installed(executable) for executable in aliases):
            detected.append(AgentOption(label, command, agent_type))
    return detected


class _AgentGrid(Widget):
    """Three-column selectable agent card grid."""

    can_focus = True
    CARD_H = 5
    ROW_GAP = 1
    GUTTER = 2
    COLS = 3

    BINDINGS = [
        ("left", "move_left", ""),
        ("right", "move_right", ""),
        ("up", "move_up", ""),
        ("down", "move_down", ""),
        ("enter", "open_selected", ""),
    ]

    class Selected(Message):
        def __init__(self, option: AgentOption) -> None:
            super().__init__()
            self.option = option

    DEFAULT_CSS = """
    _AgentGrid {
        width: 1fr;
        height: auto;
        min-height: 18;
        background: $surface;
    }
    _AgentGrid:focus {
        background: $surface;
    }
    """

    def __init__(self, options: list[AgentOption], **kwargs) -> None:
        super().__init__(**kwargs)
        self._options = options
        self.selected_index = 0
        self.scanned = False

    def update_options(
        self,
        options: list[AgentOption],
        *,
        scanned: bool | None = None,
    ) -> None:
        self._options = options
        if scanned is not None:
            self.scanned = scanned
        if not options:
            self.selected_index = 0
        else:
            self.selected_index = min(self.selected_index, len(options) - 1)
        self.refresh(layout=True)

    def selected(self) -> AgentOption | None:
        if not self._options:
            return None
        return self._options[self.selected_index]

    def move(self, delta: int) -> None:
        if not self._options:
            return
        self.selected_index = max(
            0,
            min(self.selected_index + delta, len(self._options) - 1),
        )
        self.refresh()

    def open_selected(self) -> None:
        option = self.selected()
        if option is not None:
            self.post_message(self.Selected(option))

    def action_move_left(self) -> None:
        self.move(-1)

    def action_move_right(self) -> None:
        self.move(1)

    def action_move_up(self) -> None:
        self.move(-self.COLS)

    def action_move_down(self) -> None:
        self.move(self.COLS)

    def action_open_selected(self) -> None:
        self.open_selected()

    def on_click(self, event: events.Click) -> None:
        if not self._options:
            return
        col_w = self._card_width()
        pitch = col_w + self.GUTTER
        col = event.x // pitch
        if col >= self.COLS or event.x % pitch >= col_w:
            return
        block_h = self.CARD_H + self.ROW_GAP
        row = event.y // block_h
        if event.y % block_h >= self.CARD_H:
            return
        idx = row * self.COLS + col
        if 0 <= idx < len(self._options):
            self.selected_index = idx
            self.refresh()
            self.open_selected()
            event.stop()

    def render_line(self, y: int) -> Strip:
        if not self._options:
            key = "agent.detect_empty" if self.scanned else "agent.detect_hint"
            return Strip([Segment(t(key), Style(color="bright_black"))])

        block_h = self.CARD_H + self.ROW_GAP
        row = y // block_h
        line_in_card = y % block_h
        col_w = self._card_width()
        bg = Style(bgcolor="#071226")
        if line_in_card >= self.CARD_H:
            return Strip([Segment(" " * self.size.width, bg)])

        segments: list[Segment] = []
        for col in range(self.COLS):
            idx = row * self.COLS + col
            if idx >= len(self._options):
                text, style = " " * col_w, bg
            else:
                text, style = self._card_line(
                    self._options[idx], idx, line_in_card, col_w
                )
            segments.append(Segment(text, style))
            if col < self.COLS - 1:
                segments.append(Segment(" " * self.GUTTER, bg))
        return Strip(segments)

    def _card_width(self) -> int:
        gutter_total = self.GUTTER * (self.COLS - 1)
        return max(22, (max(self.size.width, 1) - gutter_total) // self.COLS)

    def _card_line(
        self,
        option: AgentOption,
        idx: int,
        line: int,
        width: int,
    ) -> tuple[str, Style]:
        selected = idx == self.selected_index
        body = Style(
            color="#001018" if selected else "#c8f4ff",
            bgcolor="#b8f4ff" if selected else "#101a30",
            bold=selected,
        )
        muted = Style(
            color="#003342" if selected else "#8aa0b8",
            bgcolor="#b8f4ff" if selected else "#101a30",
        )
        border = Style(
            color="#00e5ff" if selected else "#314b68",
            bgcolor="#b8f4ff" if selected else "#101a30",
            bold=selected,
        )
        title = _fit(option.label, max(10, width - 4))
        command = _fit(option.command, max(10, width - 4))
        source = t(f"agent.source_{option.source}")
        if line == 0:
            return _fit("╭" + "─" * (width - 2) + "╮", width), border
        if line == 1:
            return _fit(f"│ {title}", width - 1) + "│", body
        if line == 2:
            return _fit(f"│ {command}", width - 1) + "│", muted
        if line == 3:
            return _fit(f"│ {source}", width - 1) + "│", muted
        return _fit("╰" + "─" * (width - 2) + "╯", width), border


class NewAgentModal(ModalScreen[AgentConfig | None]):
    """全屏 Modal — 选择 Agent 类型或输入自定义命令，返回 AgentConfig。

    Dismiss with None 表示用户取消（Escape）。
    """

    BINDINGS = [
        ("escape", "cancel", ""),
        ("left", "move_left", ""),
        ("right", "move_right", ""),
        ("up", "move_up", ""),
        ("down", "move_down", ""),
        ("enter", "open_selected", ""),
    ]

    DEFAULT_CSS = """
    NewAgentModal {
        align: center middle;
    }
    NewAgentModal #modal-box {
        width: 94;
        height: 90vh;
        border: round $accent;
        background: $surface;
        padding: 1 2;
    }
    NewAgentModal #agent-grid-scroll {
        height: 1fr;
        overflow-y: auto;
        background: $surface;
    }
    NewAgentModal #modal-title {
        width: 1fr;
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    NewAgentModal #btn-detect {
        width: 1fr;
        margin-top: 1;
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
    NewAgentModal #btn-add-custom {
        width: 1fr;
    }
    NewAgentModal #btn-ok {
        width: 1fr;
    }
    NewAgentModal #btn-cancel {
        width: 1fr;
    }
    """

    def __init__(
        self,
        *,
        detector: Callable[[], list[AgentOption]] = detect_installed_agents,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._detector = detector
        self._options: list[AgentOption] = []

    def compose(self) -> ComposeResult:
        with Widget(id="modal-box"):
            yield Label(t("agent.modal_title"), id="modal-title")
            with VerticalScroll(id="agent-grid-scroll"):
                yield _AgentGrid(self._options, id="agent-grid")
            yield Button(t("agent.btn_detect"), id="btn-detect")
            yield Label(t("agent.custom_label"), id="custom-label")
            yield Input(placeholder="e.g. opencode / python agent.py", id="custom-input")
            with Widget(id="btn-row"):
                yield Button(t("agent.btn_add_custom"), id="btn-add-custom")
                yield Button(t("agent.btn_start"), id="btn-ok", variant="success")
                yield Button(t("agent.btn_cancel"), id="btn-cancel", variant="error")

    def on_mount(self) -> None:
        self.query_one(_AgentGrid).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        btn_id = event.button.id

        if btn_id == "btn-cancel":
            self.dismiss(None)
            return

        if btn_id == "btn-detect":
            self._options = self._detector()
            self.query_one(_AgentGrid).update_options(self._options, scanned=True)
            return

        if btn_id == "btn-add-custom":
            self._add_custom_agent()
            return

        if btn_id == "btn-ok":
            cmd = self.query_one("#custom-input", Input).value.strip()
            if cmd:
                option = self._add_custom_agent()
                if option is not None:
                    self._launch(option)
                return
            option = self.query_one(_AgentGrid).selected()
            if option is not None:
                self._launch(option)
            return

    def on__agent_grid_selected(self, msg: _AgentGrid.Selected) -> None:
        msg.stop()
        self._launch(msg.option)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)
            event.stop()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_move_left(self) -> None:
        self.query_one(_AgentGrid).move(-1)

    def action_move_right(self) -> None:
        self.query_one(_AgentGrid).move(1)

    def action_move_up(self) -> None:
        self.query_one(_AgentGrid).move(-_AgentGrid.COLS)

    def action_move_down(self) -> None:
        self.query_one(_AgentGrid).move(_AgentGrid.COLS)

    def action_open_selected(self) -> None:
        self.query_one(_AgentGrid).open_selected()

    def _add_custom_agent(self) -> AgentOption | None:
        command = self.query_one("#custom-input", Input).value.strip()
        if not command:
            return None
        executable = _command_executable(command)
        label = executable.rsplit("/", 1)[-1] or "Custom"
        option = AgentOption(
            label=label,
            command=command,
            agent_type="custom",
            source="custom",
        )
        self._options = [
            item
            for item in self._options
            if not (item.source == "custom" and item.command == command)
        ]
        self._options.append(option)
        grid = self.query_one(_AgentGrid)
        grid.update_options(self._options)
        grid.selected_index = len(self._options) - 1
        grid.refresh()
        return option

    def _launch(self, option: AgentOption) -> None:
        self.dismiss(
            AgentConfig(
                command=option.command,
                title=option.label,
                agent_type=option.agent_type,
            )
        )


def _fit(text: str, width: int) -> str:
    if width <= 0:
        return ""
    if cell_len(text) > width:
        text = set_cell_size(text, max(0, width - 1)).rstrip() + "…"
    return set_cell_size(text, width)
