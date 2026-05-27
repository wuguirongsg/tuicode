from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static
from textual.events import Click


class MenuBar(Widget):
    DEFAULT_CSS = """
    MenuBar {
        dock: top;
        height: 1;
        layout: horizontal;
        background: $panel;
        padding: 0 1;
        border-bottom: solid $panel-lighten-1;
    }
    MenuBar .brand {
        width: auto;
        padding: 0 2;
        color: $primary;
        text-style: bold;
    }
    MenuBar .menu-sep {
        width: 1;
        color: $panel-lighten-2;
    }
    MenuBar .menu-item {
        width: auto;
        padding: 0 2;
        color: $text-muted;
    }
    MenuBar .menu-item:hover {
        background: $surface;
        color: $text;
    }
    """

    _ITEMS: list[str] = ["File", "Edit", "View", "Agents", "Help"]

    def compose(self) -> ComposeResult:
        yield Static("◈ TUICODE", classes="brand")
        yield Static("│", classes="menu-sep")
        for label in self._ITEMS:
            yield Static(label, classes="menu-item")

    def on_click(self, event: Click) -> None:
        node = event.widget
        if isinstance(node, Static) and "menu-item" in (node.classes or set()):
            self.app.notify(f"{node.render()}（菜单待实现）")
