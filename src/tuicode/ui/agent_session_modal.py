"""Agent session history picker."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Button, Label, Static

from tuicode.agent_memory import AgentSessionRecord
from tuicode.i18n import t


class AgentSessionHistoryModal(ModalScreen[AgentSessionRecord | None]):
    """Pick a previous project Agent session to continue."""

    DEFAULT_CSS = """
    AgentSessionHistoryModal {
        align: center middle;
    }
    AgentSessionHistoryModal #history-box {
        width: 76;
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
                updated = session.updated_at.replace("T", " ")[:19]
                label = (
                    f"{updated}  {session.title}  "
                    f"[{session.agent_type}/{session.status}]  {session.session_id}"
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
                self.dismiss(self._sessions[idx])

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)
            event.stop()
