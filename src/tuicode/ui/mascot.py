"""右栏吉祥物面板 — Braille 像素艺术机器人，4 行显示 + 状态标签。"""
from __future__ import annotations

from textual.timer import Timer
from textual.widget import Widget
from textual.widgets import Static
from textual.app import ComposeResult

from tuicode.i18n import t

# ── Braille 编码器 ────────────────────────────────────────────────────────────
# Unicode Braille 点位映射（U+2800 base）:
#  dot1(bit0) dot2(bit1) dot3(bit2) dot7(bit6)
#  dot4(bit3) dot5(bit4) dot6(bit5) dot8(bit7)
# 每个字符覆盖 2 列 × 4 行像素
_BRAILLE_MAP = [
    [0x01, 0x08],  # row0: dot1, dot4
    [0x02, 0x10],  # row1: dot2, dot5
    [0x04, 0x20],  # row2: dot3, dot6
    [0x40, 0x80],  # row3: dot7, dot8
]


def _to_braille(rows: list[str]) -> list[str]:
    """将 '#'/'.' 像素网格（len(rows)%4==0，len(row)%2==0）转为 Braille 行列表。"""
    result: list[str] = []
    for r in range(0, len(rows), 4):
        chunk = rows[r:r + 4]
        width = len(chunk[0])
        line = ""
        for c in range(0, width, 2):
            bits = 0
            for dr in range(4):
                for dc in range(2):
                    row = chunk[dr] if dr < len(chunk) else ""
                    if c + dc < len(row) and row[c + dc] == "#":
                        bits |= _BRAILLE_MAP[dr][dc]
            line += chr(0x2800 + bits)
        result.append(line)
    return result


# ── 像素帧定义（40 像素宽 × 16 像素高）───────────────────────────────────────
_E = "........................................"  # 40 空白行

# 固定行（头部 / 颈部 / 躯干 / 底部）
_H0 = "...################################....."  # head top
_H1 = "...#..............................#....."  # head interior
_NK = "..........##################............"  # neck
_B0 = "...............##########..............."  # body top
_B1 = "...............#........#..............."
_B2 = "...............#........#..............."
_B3 = "...............##########..............."  # body bottom

# 眼睛行变体（rows 3 & 4 → 眼睛区域）
_EYE_OPEN   = ("...#...####...........####........#.....",
               "...#...####...........####........#.....")
_EYE_BLINK  = ("...#..............................#.....",
               "...#..............................#.....")
_EYE_BLINK2 = ("...#....##.............##.........#.....",
               "...#....##.............##.........#.....")
_EYE_WIDE   = ("...#..######.........######.......#.....",
               "...#..######.........######.......#.....")
_EYE_STAR_A = ("...#..##.##..........##.##........#.....",
               "...#..##.##..........##.##........#.....")
_EYE_STAR_B = ("...#...####..........####.........#.....",
               "...#...####..........####.........#.....")
_EYE_X      = ("...#..##..##.........##..##.......#.....",
               "...#..##..##.........##..##.......#.....")

# 嘴巴行变体（row 7 → 嘴巴区域）
_MOUTH_NEUTRAL = "...#.........############.........#....."
_MOUTH_HAPPY   = "...#........#.##########.#........#....."
_MOUTH_SAD     = "...#......################........#....."
_MOUTH_OPEN    = "...#.......##..........##.........#....."


def _build_frame(eyes: tuple[str, str], mouth: str) -> list[str]:
    """拼合完整的 16 行像素帧。"""
    return [
        _H0, _H1,       # row  0-1  头顶
        _H1,            # row  2    头部内部
        eyes[0],        # row  3    眼睛上半
        eyes[1],        # row  4    眼睛下半
        _H1,            # row  5    鼻子区
        _H1,            # row  6
        mouth,          # row  7    嘴巴
        _H1,            # row  8
        _H0,            # row  9    头底（复用头顶）
        _NK,            # row 10    颈部
        _B0,            # row 11    躯干顶
        _B1,            # row 12
        _B2,            # row 13
        _B3,            # row 14    躯干底
        _E,             # row 15    空白
    ]


# 预计算所有帧的 Braille 字符串（4 行 × 20 字符宽）
_FRAMES: dict[str, list[str]] = {
    k: _to_braille(_build_frame(eyes, mouth))
    for k, (eyes, mouth) in {
        "idle_1":    (_EYE_OPEN,   _MOUTH_NEUTRAL),
        "idle_2":    (_EYE_BLINK,  _MOUTH_NEUTRAL),
        "wide_1":    (_EYE_WIDE,   _MOUTH_HAPPY),
        "wide_2":    (_EYE_WIDE,   _MOUTH_OPEN),
        "agent_1":   (_EYE_STAR_A, _MOUTH_NEUTRAL),
        "agent_2":   (_EYE_STAR_B, _MOUTH_NEUTRAL),
        "success":   (_EYE_WIDE,   _MOUTH_HAPPY),
        "error_1":   (_EYE_X,      _MOUTH_SAD),
        "error_2":   (_EYE_BLINK2, _MOUTH_SAD),
    }.items()
}

# ── 状态配置 ─────────────────────────────────────────────────────────────────
# (秒/帧, 帧名列表, 颜色, i18n key)
_TICK = 0.28

_STATE_CFG: dict[str, tuple[float, list[str], str, str]] = {
    "idle":    (1.2,  ["idle_1", "idle_2"],   "#00d4ff", "mascot.idle"),
    "opening": (0.20, ["wide_1", "wide_2"],   "#00d4ff", "mascot.opening"),
    "running": (0.30, ["wide_1", "wide_2"],   "#00ff41", "mascot.running"),
    "agent":   (0.20, ["agent_1", "agent_2"], "#bf00ff", "mascot.agent"),
    "success": (1.50, ["success"],            "#00ff41", "mascot.success"),
    "error":   (0.35, ["error_1", "error_2"], "#ff003c", "mascot.error"),
}


class MascotPanel(Widget):
    """右栏吉祥物面板：4 行 Braille 机器人 + 1 行状态标签，共占 5 行。"""

    DEFAULT_CSS = """
    MascotPanel {
        height: 6;
        width: 1fr;
        background: $panel;
        border-bottom: solid $panel-lighten-1;
        padding: 0 0;
        layout: vertical;
    }
    MascotPanel #mp-art {
        height: 4;
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
        spf, frame_names, color, key = _STATE_CFG[self._state]
        ticks_per_frame = max(1, round(spf / _TICK))
        fname = frame_names[(self._ticks // ticks_per_frame) % len(frame_names)]
        braille_rows = _FRAMES[fname]

        if self._state == "idle":
            art = "\n".join(f"[dim #00d4ff]{row}[/]" for row in braille_rows)
            label = f"[dim]{t(key)}[/]"
        else:
            art = "\n".join(f"[bold {color}]{row}[/]" for row in braille_rows)
            label = f"[bold {color}]{t(key)}[/]"

        self.query_one("#mp-art", Static).update(art)
        self.query_one("#mp-label", Static).update(label)

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
