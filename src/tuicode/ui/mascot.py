"""右栏吉祥物面板 — Braille 像素艺术机器人，4 行显示 + 状态标签。"""
from __future__ import annotations

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
    """'#'/'.' 像素网格（16 行 × 40 列）→ Braille 字符行列表（4 行 × 20 字符）。"""
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


# ── 像素帧定义（40 列 × 16 行）────────────────────────────────────────────────
#
# 头部居中：pos 12-27（16 像素宽），内部 pos 13-26（14 像素宽）
# 左眼：pos 15-16  右眼：pos 23-24（2×2，对称）
# 宽眼：pos 14-17  右宽眼：pos 22-25（4×2，对称）
# 嘴巴：pos 18-21（4 像素宽，居中）
# 身体：pos 17-22（6 像素宽，居中于头部下方）
# 3 对腿：内层 row8-11 / 中层 row10-13 / 外层 row12-15

_H0 = "............################............"  # 头部上/下边框（16 宽）
_HI = "............#..............#............"  # 头部内部空行

# 眼睛行对（row2, row3）
_EYE_OPEN  = ("............#..##......##..#............",
              "............#..##......##..#............")
_EYE_BLINK = ("............#..............#............",
              "............#..............#............")
_EYE_HALF  = ("............#..##......##..#............",
              "............#..............#............")
_EYE_WIDE  = ("............#.####....####.#............",
              "............#.####....####.#............")

# 嘴巴行（row5）
_MOUTH_NEUTRAL = "............#.....####.....#............"  # 4 宽横线
_MOUTH_HAPPY   = "............#....######....#............"  # 6 宽宽嘴
_MOUTH_SAD     = "............#......##......#............"  # 2 宽小嘴
_MOUTH_OPEN    = "............#....##..##....#............"  # O 形

# 腿部固定行（row 8-15）：3 对腿分层展开
_L0 = ".............##..######..##............."  # 内层腿 row8
_L1 = "............##...######...##............"  # 内层腿 row9
_L2 = ".......##..##....######....##..##......."  # 中+内层 row10
_L3 = "......##..##.....######.....##..##......"  # 中+内层 row11
_L4 = "..##.##..##......######......##..##.##.."  # 全3对 row12
_L5 = ".##.##..##.......######.......##..##.##."  # 全3对 row13
_L6 = "##...............######...............##"  # 外层腿 row14
_L7 = "........................................"  # 空行 row15


def _build_frame(eyes: tuple[str, str], mouth: str) -> list[str]:
    return [
        _H0,       # row 0  头顶边框
        _HI,       # row 1  内部
        eyes[0],   # row 2  眼睛上半
        eyes[1],   # row 3  眼睛下半
        _HI,       # row 4  内部
        mouth,     # row 5  嘴巴
        _HI,       # row 6  内部
        _H0,       # row 7  头底边框
        _L0,       # row 8  内层腿
        _L1,       # row 9
        _L2,       # row 10 中层腿出现
        _L3,       # row 11
        _L4,       # row 12 外层腿出现
        _L5,       # row 13
        _L6,       # row 14 外层腿末端
        _L7,       # row 15 空
    ]


# 预计算所有帧的 Braille 字符串
_FRAMES: dict[str, list[str]] = {
    k: _to_braille(_build_frame(eyes, mouth))
    for k, (eyes, mouth) in {
        "idle_1":  (_EYE_OPEN,  _MOUTH_NEUTRAL),
        "idle_2":  (_EYE_BLINK, _MOUTH_NEUTRAL),
        "wide_1":  (_EYE_WIDE,  _MOUTH_HAPPY),
        "wide_2":  (_EYE_WIDE,  _MOUTH_OPEN),
        "agent_1": (_EYE_WIDE,  _MOUTH_NEUTRAL),
        "agent_2": (_EYE_OPEN,  _MOUTH_NEUTRAL),
        "success": (_EYE_WIDE,  _MOUTH_HAPPY),
        "error_1": (_EYE_HALF,  _MOUTH_SAD),
        "error_2": (_EYE_BLINK, _MOUTH_SAD),
    }.items()
}

# ── 状态配置 ─────────────────────────────────────────────────────────────────
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
