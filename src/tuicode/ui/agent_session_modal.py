"""Agent session history picker and review modal."""
from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual import events
from textual.message import Message
from textual.screen import ModalScreen
from textual.strip import Strip
from textual.widget import Widget
from textual.widgets import Button, Label, Static

from rich.cells import cell_len, set_cell_size
from rich.segment import Segment
from rich.style import Style

from tuicode.agent_memory import (
    AgentSessionRecord,
    session_brief,
    session_description,
    session_detail,
)
from tuicode.i18n import t

DetailAction = Literal["continue", "delete", "back"]


class AgentSessionDetailModal(ModalScreen[DetailAction]):
    """Show a saved session before the user decides what to do with it."""

    DEFAULT_CSS = """
    AgentSessionDetailModal {
        align: center middle;
    }
    AgentSessionDetailModal #detail-box {
        width: 78;
        height: 88vh;
        border: round $accent;
        background: $surface;
        padding: 1 2;
    }
    AgentSessionDetailModal #detail-title {
        width: 1fr;
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    AgentSessionDetailModal #detail-scroll {
        height: 1fr;
        overflow-y: auto;
        background: $panel;
        padding: 0 1;
    }
    AgentSessionDetailModal #detail-actions {
        layout: horizontal;
        height: auto;
        margin-top: 1;
    }
    AgentSessionDetailModal #detail-continue {
        width: 1fr;
    }
    AgentSessionDetailModal #detail-delete {
        width: 1fr;
    }
    AgentSessionDetailModal #detail-back {
        width: 1fr;
    }
    """

    def __init__(self, session: AgentSessionRecord, **kwargs) -> None:
        super().__init__(**kwargs)
        self._session = session

    def compose(self) -> ComposeResult:
        with Widget(id="detail-box"):
            yield Label(t("agent.detail_title"), id="detail-title")
            with VerticalScroll(id="detail-scroll"):
                yield Static(session_detail(self._session), id="detail-body")
            with Widget(id="detail-actions"):
                yield Button(
                    t("agent.btn_continue"),
                    id="detail-continue",
                    variant="success",
                )
                yield Button(
                    t("agent.btn_delete"),
                    id="detail-delete",
                    variant="error",
                )
                yield Button(t("agent.btn_back"), id="detail-back")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "detail-continue":
            self.dismiss("continue")
        elif event.button.id == "detail-delete":
            self.dismiss("delete")
        elif event.button.id == "detail-back":
            self.dismiss("back")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss("back")
            event.stop()


class _SessionGrid(Widget):
    """Three-column selectable session card grid."""

    can_focus = True
    CARD_H = 6
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
        def __init__(self, session: AgentSessionRecord) -> None:
            super().__init__()
            self.session = session

    DEFAULT_CSS = """
    _SessionGrid {
        width: 1fr;
        height: auto;
        min-height: 22;
        background: $surface;
    }
    _SessionGrid:focus {
        background: $surface;
    }
    """

    def __init__(self, sessions: list[AgentSessionRecord], **kwargs) -> None:
        super().__init__(**kwargs)
        self._sessions = sessions
        self.selected_index = 0

    def update_sessions(self, sessions: list[AgentSessionRecord]) -> None:
        self._sessions = sessions
        if not sessions:
            self.selected_index = 0
        else:
            self.selected_index = min(self.selected_index, len(sessions) - 1)
        self.refresh(layout=True)

    def move(self, delta: int) -> None:
        if not self._sessions:
            return
        self.selected_index = max(
            0,
            min(self.selected_index + delta, len(self._sessions) - 1),
        )
        self.refresh()

    def open_selected(self) -> None:
        if not self._sessions:
            return
        self.post_message(self.Selected(self._sessions[self.selected_index]))

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
        if not self._sessions:
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
        if 0 <= idx < len(self._sessions):
            self.selected_index = idx
            self.refresh()
            self.open_selected()
            event.stop()

    def render_line(self, y: int) -> Strip:
        if not self._sessions:
            return Strip([Segment(t("agent.history_empty"), Style(color="bright_black"))])

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
            if idx >= len(self._sessions):
                text, style = " " * col_w, bg
            else:
                text, style = self._card_line(
                    self._sessions[idx], idx, line_in_card, col_w
                )
            segments.append(Segment(text, style))
            if col < self.COLS - 1:
                segments.append(Segment(" " * self.GUTTER, bg))
        return Strip(segments)

    def _card_width(self) -> int:
        gutter_total = self.GUTTER * (self.COLS - 1)
        return max(26, (max(self.size.width, 1) - gutter_total) // self.COLS)

    def _card_line(
        self,
        session: AgentSessionRecord,
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
        title = session_brief(session, max_len=max(10, width - 4))
        desc = session_description(session, max_len=max(10, width - 4))
        meta = (
            f"{session.updated_at.replace('T', ' ')[:10]} "
            f"{session.agent_type} {session.status}"
        )
        if line == 0:
            return _fit("╭" + "─" * (width - 2) + "╮", width), border
        if line == 1:
            return _fit(f"│ {title}", width - 1) + "│", body
        if line == 2:
            return _fit(f"│ {desc}", width - 1) + "│", muted
        if line == 3:
            return _fit(f"│ {meta}", width - 1) + "│", muted
        if line == 4:
            return _fit("│", width - 1) + "│", body
        return _fit("╰" + "─" * (width - 2) + "╯", width), border


class AgentSessionHistoryModal(ModalScreen[AgentSessionRecord | None]):
    """Pick a previous project Agent session, review it, then continue."""

    BINDINGS = [
        ("escape", "cancel", ""),
        ("left", "move_left", ""),
        ("right", "move_right", ""),
        ("up", "move_up", ""),
        ("down", "move_down", ""),
        ("enter", "open_selected", ""),
    ]

    DEFAULT_CSS = """
    AgentSessionHistoryModal {
        align: center middle;
    }
    AgentSessionHistoryModal #history-box {
        width: 94;
        height: 88vh;
        border: round $accent;
        background: $surface;
        padding: 1 2;
    }
    AgentSessionHistoryModal #history-title {
        width: 1fr;
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    AgentSessionHistoryModal #history-grid-scroll {
        height: 1fr;
        overflow-y: auto;
        background: $surface;
    }
    AgentSessionHistoryModal #history-cancel {
        width: 1fr;
        margin-top: 1;
    }
    """

    def __init__(
        self,
        sessions: list[AgentSessionRecord],
        on_delete: Callable[[str], bool] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._sessions = sessions
        self._on_delete = on_delete

    def compose(self) -> ComposeResult:
        with Widget(id="history-box"):
            yield Label(t("agent.history_title"), id="history-title")
            with VerticalScroll(id="history-grid-scroll"):
                yield _SessionGrid(self._sessions, id="session-grid")
            yield Button(t("agent.btn_cancel"), id="history-cancel", variant="error")

    def on_mount(self) -> None:
        self.query_one(_SessionGrid).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "history-cancel":
            self.dismiss(None)

    def on__session_grid_selected(self, msg: _SessionGrid.Selected) -> None:
        msg.stop()
        self._open_detail(msg.session)

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_move_left(self) -> None:
        self.query_one(_SessionGrid).move(-1)

    def action_move_right(self) -> None:
        self.query_one(_SessionGrid).move(1)

    def action_move_up(self) -> None:
        self.query_one(_SessionGrid).move(-_SessionGrid.COLS)

    def action_move_down(self) -> None:
        self.query_one(_SessionGrid).move(_SessionGrid.COLS)

    def action_open_selected(self) -> None:
        self.query_one(_SessionGrid).open_selected()

    def _open_detail(self, session: AgentSessionRecord) -> None:
        self.app.push_screen(
            AgentSessionDetailModal(session),
            lambda action: self._on_detail_closed(session, action),
        )

    def _on_detail_closed(
        self, session: AgentSessionRecord, action: DetailAction | None
    ) -> None:
        if action == "continue":
            self.dismiss(session)
        elif action == "delete":
            self._delete_session(session)

    def _delete_session(self, session: AgentSessionRecord) -> None:
        if self._on_delete is not None:
            self._on_delete(session.session_id)
        self._sessions = [
            item for item in self._sessions if item.session_id != session.session_id
        ]
        self.query_one(_SessionGrid).update_sessions(self._sessions)


def _fit(text: str, width: int) -> str:
    if width <= 0:
        return ""
    if cell_len(text) > width:
        text = set_cell_size(text, max(0, width - 1)).rstrip() + "…"
    return set_cell_size(text, width)
