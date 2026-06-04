"""右栏吉祥物面板 — 彩色 Braille LED 点阵屏，跑马灯 + 状态动画。"""
from __future__ import annotations

from dataclasses import dataclass

from rich.markup import escape
from textual.events import Click
from textual.timer import Timer
from textual.widget import Widget
from textual.widgets import Static
from textual.app import ComposeResult

from tuicode.i18n import t

# ── Braille 编码器 ────────────────────────────────────────────────────────────
# 点位映射（U+2800 base）：左列 col0 / 右列 col1，每 4 行为一组
_BRAILLE_MAP = [
    [0x01, 0x08],  # row0: dot1, dot4
    [0x02, 0x10],  # row1: dot2, dot5
    [0x04, 0x20],  # row2: dot3, dot6
    [0x40, 0x80],  # row3: dot7, dot8
]


def _to_braille(rows: list[str]) -> list[str]:
    """'#'/'.' 像素网格 → Braille 字符行列表。"""
    result: list[str] = []
    for r in range(0, len(rows), 4):
        chunk = rows[r:r + 4]
        width = len(chunk[0])
        line = ""
        for c in range(0, width, 2):
            bits = 0
            for dr in range(4):
                row_str = chunk[dr] if dr < len(chunk) else ""
                for dc in range(2):
                    if c + dc < len(row_str) and row_str[c + dc] == "#":
                        bits |= _BRAILLE_MAP[dr][dc]
            line += chr(0x2800 + bits)
        result.append(line)
    return result


# ── LED 点阵屏 ────────────────────────────────────────────────────────────────
_SCREEN_WIDTH = 40
_SCREEN_HEIGHT = 12
_TEXT_TOP = 3

_FONT_3X5: dict[str, tuple[str, ...]] = {
    "A": ("###", "#.#", "###", "#.#", "#.#"),
    "B": ("##.", "#.#", "##.", "#.#", "##."),
    "C": ("###", "#..", "#..", "#..", "###"),
    "D": ("##.", "#.#", "#.#", "#.#", "##."),
    "E": ("###", "#..", "##.", "#..", "###"),
    "F": ("###", "#..", "##.", "#..", "#.."),
    "G": ("###", "#..", "#.#", "#.#", "###"),
    "H": ("#.#", "#.#", "###", "#.#", "#.#"),
    "I": ("###", ".#.", ".#.", ".#.", "###"),
    "J": ("..#", "..#", "..#", "#.#", "###"),
    "K": ("#.#", "#.#", "##.", "#.#", "#.#"),
    "L": ("#..", "#..", "#..", "#..", "###"),
    "M": ("#.#", "###", "###", "#.#", "#.#"),
    "N": ("#.#", "###", "###", "###", "#.#"),
    "O": ("###", "#.#", "#.#", "#.#", "###"),
    "P": ("###", "#.#", "###", "#..", "#.."),
    "Q": ("###", "#.#", "#.#", "###", "..#"),
    "R": ("###", "#.#", "###", "##.", "#.#"),
    "S": ("###", "#..", "###", "..#", "###"),
    "T": ("###", ".#.", ".#.", ".#.", ".#."),
    "U": ("#.#", "#.#", "#.#", "#.#", "###"),
    "V": ("#.#", "#.#", "#.#", "#.#", ".#."),
    "W": ("#.#", "#.#", "###", "###", "#.#"),
    "X": ("#.#", "#.#", ".#.", "#.#", "#.#"),
    "Y": ("#.#", "#.#", ".#.", ".#.", ".#."),
    "Z": ("###", "..#", ".#.", "#..", "###"),
    "0": ("###", "#.#", "#.#", "#.#", "###"),
    "1": (".#.", "##.", ".#.", ".#.", "###"),
    "2": ("###", "..#", "###", "#..", "###"),
    "3": ("###", "..#", "###", "..#", "###"),
    "4": ("#.#", "#.#", "###", "..#", "..#"),
    "5": ("###", "#..", "###", "..#", "###"),
    "6": ("###", "#..", "###", "#.#", "###"),
    "7": ("###", "..#", "..#", ".#.", ".#."),
    "8": ("###", "#.#", "###", "#.#", "###"),
    "9": ("###", "#.#", "###", "..#", "###"),
    ":": ("...", ".#.", "...", ".#.", "..."),
    ".": ("...", "...", "...", "...", ".#."),
    "-": ("...", "...", "###", "...", "..."),
    "/": ("..#", "..#", ".#.", "#..", "#.."),
    "+": ("...", ".#.", "###", ".#.", "..."),
    "!": (".#.", ".#.", ".#.", "...", ".#."),
    "?": ("###", "..#", ".#.", "...", ".#."),
    " ": ("...", "...", "...", "...", "..."),
}

_PALETTES: dict[str, tuple[str, ...]] = {
    "cyan": ("#00d4ff", "#00fff0", "#5eead4", "#7dd3fc"),
    "green": ("#00ff41", "#82ff6a", "#c6ff00", "#00ffa3"),
    "violet": ("#bf00ff", "#ff4dff", "#00d4ff", "#9f7aea"),
    "gold": ("#ffe66d", "#ffb703", "#00ff41", "#00d4ff"),
    "red": ("#ff003c", "#ff6b35", "#ff9f1c", "#ff003c"),
}


@dataclass(frozen=True)
class _LedState:
    message: str
    palette: str
    mode: str
    label_key: str


# ── 状态配置 ─────────────────────────────────────────────────────────────────
_TICK = 0.28

_STATE_CFG: dict[str, _LedState] = {
    "idle": _LedState("TUICODE  READY", "cyan", "marquee", "mascot.idle"),
    "opening": _LedState("READING  FILE", "cyan", "scan", "mascot.opening"),
    "running": _LedState("RUNNING  TASK", "green", "wave", "mascot.running"),
    "agent": _LedState("AGENT  THINKING", "violet", "compute", "mascot.agent"),
    "success": _LedState("DONE  OK", "gold", "spark", "mascot.success"),
    "error": _LedState("ERROR  CHECK", "red", "alert", "mascot.error"),
}


def _blank_screen() -> list[list[str]]:
    return [["." for _ in range(_SCREEN_WIDTH)] for _ in range(_SCREEN_HEIGHT)]


def _text_pixels(text: str) -> list[str]:
    rows = ["" for _ in range(5)]
    for ch in text.upper():
        glyph = _FONT_3X5.get(ch, _FONT_3X5["?"])
        for index, row in enumerate(glyph):
            rows[index] += row + "."
    return rows


def _draw_marquee(screen: list[list[str]], text: str, tick: int) -> None:
    text_rows = _text_pixels(text)
    gap = "." * _SCREEN_WIDTH
    strip_width = len(text_rows[0]) + _SCREEN_WIDTH
    offset = tick % max(1, strip_width)
    for row_index, row in enumerate(text_rows):
        strip = row + gap
        visible = strip[offset:offset + _SCREEN_WIDTH]
        visible = visible.ljust(_SCREEN_WIDTH, ".")
        for col, pixel in enumerate(visible):
            if pixel == "#":
                screen[_TEXT_TOP + row_index][col] = "#"


def _draw_scan(screen: list[list[str]], tick: int) -> None:
    col = (tick * 3) % _SCREEN_WIDTH
    for row in range(_SCREEN_HEIGHT):
        screen[row][col] = "#"
        if col > 0 and row % 2 == 0:
            screen[row][col - 1] = "#"


def _draw_wave(screen: list[list[str]], tick: int) -> None:
    for col in range(_SCREEN_WIDTH):
        if (col + tick) % 4 == 0:
            screen[0][col] = "#"
        if (col - tick) % 5 == 0:
            screen[_SCREEN_HEIGHT - 1][col] = "#"
    for index in range(5):
        col = (tick * 2 + index * 7) % _SCREEN_WIDTH
        screen[1 + index % 2][col] = "#"
        screen[9 + index % 2][(_SCREEN_WIDTH - 1) - col] = "#"


def _draw_compute(screen: list[list[str]], tick: int) -> None:
    for col in range(_SCREEN_WIDTH):
        if (col * 3 + tick) % 7 == 0:
            screen[0][col] = "#"
        if (col * 5 + tick) % 11 == 0:
            screen[1][col] = "#"
        if (col * 2 - tick) % 9 == 0:
            screen[10][col] = "#"
        if (col + tick) % 6 == 0:
            screen[11][col] = "#"


def _draw_spark(screen: list[list[str]], tick: int) -> None:
    anchors = (4, 11, 19, 28, 35)
    for index, col in enumerate(anchors):
        radius = (tick + index) % 3
        row = 1 + (index % 4) * 3
        for dr, dc in ((0, 0), (-radius, 0), (radius, 0), (0, -radius), (0, radius)):
            rr = row + dr
            cc = col + dc
            if 0 <= rr < _SCREEN_HEIGHT and 0 <= cc < _SCREEN_WIDTH:
                screen[rr][cc] = "#"


def _draw_alert(screen: list[list[str]], tick: int) -> None:
    if tick % 2 == 0:
        for col in range(_SCREEN_WIDTH):
            screen[0][col] = "#"
            screen[_SCREEN_HEIGHT - 1][col] = "#"
        for row in range(_SCREEN_HEIGHT):
            screen[row][0] = "#"
            screen[row][_SCREEN_WIDTH - 1] = "#"


def _render_led_frame(state: str, tick: int) -> list[str]:
    cfg = _STATE_CFG[state if state in _STATE_CFG else "idle"]
    screen = _blank_screen()
    if cfg.mode == "scan":
        _draw_scan(screen, tick)
    elif cfg.mode == "wave":
        _draw_wave(screen, tick)
    elif cfg.mode == "compute":
        _draw_compute(screen, tick)
    elif cfg.mode == "spark":
        _draw_spark(screen, tick)
    elif cfg.mode == "alert":
        _draw_alert(screen, tick)
    _draw_marquee(screen, cfg.message, tick)
    return _to_braille(["".join(row) for row in screen])


def _colorize_braille(rows: list[str], palette_name: str, tick: int) -> str:
    palette = _PALETTES[palette_name]
    colored_rows: list[str] = []
    for row_index, row in enumerate(rows):
        cells = []
        for col, char in enumerate(row):
            color = palette[(col + row_index + tick) % len(palette)]
            cells.append(f"[bold {color}]{escape(char)}[/]")
        colored_rows.append("".join(cells))
    return "\n".join(colored_rows)


class MascotPanel(Widget):
    """右栏 LED 点阵屏：3 行 Braille 屏幕 + 1 行状态标签，共占 5 行。"""

    DEFAULT_CSS = """
    MascotPanel {
        height: 5;
        width: 1fr;
        background: $panel;
        border-bottom: solid $panel-lighten-1;
        layout: vertical;
    }
    MascotPanel #mp-art {
        height: 3;
        width: 1fr;
        text-align: center;
    }
    MascotPanel #mp-label {
        height: 1;
        width: 1fr;
        text-align: center;
        color: $text-muted;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._state = "idle"
        self._ticks = 0
        self._reset_handle: Timer | None = None

    def compose(self) -> ComposeResult:
        yield Static("", id="mp-art")
        yield Static("", id="mp-label")

    def on_mount(self) -> None:
        self.set_interval(_TICK, self._tick)
        self._refresh_display()

    def _tick(self) -> None:
        self._ticks += 1
        self._refresh_display()

    def _refresh_display(self) -> None:
        cfg = _STATE_CFG[self._state]
        braille_rows = _render_led_frame(self._state, self._ticks)
        art = _colorize_braille(braille_rows, cfg.palette, self._ticks)

        label_color = _PALETTES[cfg.palette][self._ticks % len(_PALETTES[cfg.palette])]
        label_style = "dim" if self._state == "idle" else f"bold {label_color}"
        label = f"[{label_style}]{t(cfg.label_key)}[/]"

        self.query_one("#mp-art", Static).update(art)
        self.query_one("#mp-label", Static).update(label)

    def on_click(self, event: Click) -> None:
        event.stop()
        self.app.action_command_palette()

    def set_state(self, state: str, auto_reset: float = 0.0) -> None:
        """切换状态；auto_reset > 0 则指定秒后自动回到 idle。"""
        if self._reset_handle is not None:
            self._reset_handle.stop()
            self._reset_handle = None
        self._state = state if state in _STATE_CFG else "idle"
        self._ticks = 0
        self._refresh_display()
        if auto_reset > 0:
            self._reset_handle = self.set_timer(
                auto_reset, lambda: self.set_state("idle")
            )
