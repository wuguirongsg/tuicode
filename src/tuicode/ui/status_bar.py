from __future__ import annotations

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.timer import Timer
from textual.widget import Widget
from textual.widgets import Static

from tuicode.i18n import t

# ── 吉祥物状态表 ──────────────────────────────────────────────────────────────
# (秒/帧, 帧列表, rich颜色, i18n key)
_TICK = 0.28

_STATES: dict[str, tuple[float, list[str], str, str]] = {
    "idle":    (1.2,  ["(·_·)", "(◉_◉)"],  "",        "mascot.idle"),
    "opening": (0.22, ["(◈_◈)", "(◉_◈)"],  "#00d4ff", "mascot.opening"),
    "running": (0.32, ["(◉_◉)", "(◈_◉)"],  "#00ff41", "mascot.running"),
    "agent":   (0.22, ["(⊙_⊙)", "(◎_◎)"],  "#bf00ff", "mascot.agent"),
    "success": (1.5,  ["(◉U◉)"],           "#00ff41", "mascot.success"),
    "error":   (0.36, ["(x_x)", "(×_×)"],  "#ff003c", "mascot.error"),
}


class MascotWidget(Widget):
    """状态栏吉祥物 — 像素小机器人，随操作产生动画反馈。"""

    DEFAULT_CSS = """
    MascotWidget {
        width: auto;
        padding: 0 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._state = "idle"
        self._ticks = 0
        self._reset_handle: Timer | None = None

    def on_mount(self) -> None:
        self.set_interval(_TICK, self._tick)

    def _tick(self) -> None:
        self._ticks += 1
        self.refresh()

    def set_state(self, state: str, auto_reset: float = 0.0) -> None:
        """切换吉祥物状态。auto_reset > 0 则在指定秒数后自动回到 idle。"""
        if self._reset_handle is not None:
            self._reset_handle.stop()
            self._reset_handle = None
        self._state = state if state in _STATES else "idle"
        self._ticks = 0
        self.refresh()
        if auto_reset > 0:
            self._reset_handle = self.set_timer(
                auto_reset, lambda: self.set_state("idle")
            )

    def render(self) -> str:
        spf, frames, color, key = _STATES[self._state]
        ticks_per_frame = max(1, round(spf / _TICK))
        face = frames[(self._ticks // ticks_per_frame) % len(frames)]
        label = t(key)
        if self._state == "idle":
            return f"[dim]{face}  {label}[/]"
        return f"[bold {color}]{face}[/]  [{color}]{label}[/]"


# ── StatusBar ─────────────────────────────────────────────────────────────────


class StatusBar(Widget):
    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 1;
        layout: horizontal;
        background: $primary;
        padding: 0 1;
    }
    StatusBar #sb-left  { width: 1fr; color: $background 90%; }
    StatusBar #sb-sep   { width: 1; color: $background 40%; }
    StatusBar #sb-sep2  { width: 1; color: $background 40%; }
    StatusBar #sb-right { width: auto; color: $background 70%; }
    StatusBar MascotWidget { background: $primary; color: $background 90%; }
    """

    agent_count: reactive[int] = reactive(0)

    def __init__(self, version: str) -> None:
        super().__init__()
        self._version = version

    def compose(self) -> ComposeResult:
        yield Static(id="sb-left")
        yield Static("│", id="sb-sep")
        yield MascotWidget(id="sb-mascot")
        yield Static("│", id="sb-sep2")
        yield Static(t("status.shortcuts"), id="sb-right")

    def on_mount(self) -> None:
        self._refresh_left()

    def watch_agent_count(self, count: int) -> None:
        self._refresh_left()

    def _refresh_left(self) -> None:
        n = self.agent_count
        if n == 0:
            agent_str = t("status.no_agents")
        elif n == 1:
            agent_str = t("status.agents", n=n)
        else:
            agent_str = t("status.agents_pl", n=n)
        self.query_one("#sb-left", Static).update(
            f"TuiCode v{self._version}  {agent_str}"
        )

    def set_mascot_state(self, state: str, auto_reset: float = 0.0) -> None:
        self.query_one(MascotWidget).set_state(state, auto_reset)
