"""Agent session history picker and review modal."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Button, Label, Static

from tuicode.agent_memory import AgentSessionRecord, session_brief, session_detail
from tuicode.i18n import t


class AgentSessionDetailModal(ModalScreen[bool]):
    """Show a saved session before the user decides to continue it."""

    DEFAULT_CSS = """
    AgentSessionDetailModal {
        align: center middle;
    }
    AgentSessionDetailModal #detail-box {
        width: 84;
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
                yield Button(t("agent.btn_back"), id="detail-back")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "detail-continue":
            self.dismiss(True)
        elif event.button.id == "detail-back":
            self.dismiss(False)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(False)
            event.stop()


class AgentSessionHistoryModal(ModalScreen[AgentSessionRecord | None]):
    """Pick a previous project Agent session, review it, then continue."""

    DEFAULT_CSS = """
    AgentSessionHistoryModal {
        align: center middle;
    }
    AgentSessionHistoryModal #history-box {
        width: 82;
        height: auto;
        max-height: 88vh;
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
    AgentSessionHistoryModal .session-btn {
        width: 1fr;
        margin-bottom: 0;
    }
    AgentSessionHistoryModal #history-empty {
        color: $text-muted;
        margin-bottom: 1;
    }
    AgentSessionHistoryModal #history-cancel {
        width: 1fr;
        margin-top: 1;
    }
    """

    def __init__(self, sessions: list[AgentSessionRecord], **kwargs) -> None:
        super().__init__(**kwargs)
        self._sessions = sessions

    def compose(self) -> ComposeResult:
        with Widget(id="history-box"):
            yield Label(t("agent.history_title"), id="history-title")
            if not self._sessions:
                yield Static(t("agent.history_empty"), id="history-empty")
            for idx, session in enumerate(self._sessions):
                updated = session.updated_at.replace("T", " ")[:16]
                label = (
                    f"{t('agent.btn_view')}  {session_brief(session)}  "
                    f"[{updated} · {session.agent_type} · {session.status}]"
                )
                yield Button(label, id=f"session-{idx}", classes="session-btn")
            yield Button(t("agent.btn_cancel"), id="history-cancel", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        btn_id = event.button.id or ""
        if btn_id == "history-cancel":
            self.dismiss(None)
            return
        if btn_id.startswith("session-"):
            idx = int(btn_id.removeprefix("session-"))
            if 0 <= idx < len(self._sessions):
                session = self._sessions[idx]
                self.app.push_screen(
                    AgentSessionDetailModal(session),
                    lambda confirmed: self._on_detail_closed(session, confirmed),
                )

    def _on_detail_closed(
        self, session: AgentSessionRecord, confirmed: bool | None
    ) -> None:
        if confirmed:
            self.dismiss(session)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)
            event.stop()
