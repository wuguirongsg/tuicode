"""右栏 Braille LED 点阵屏测试。"""
from __future__ import annotations

from tuicode.ui.mascot import (
    _colorize_braille,
    _render_led_frame,
    _text_pixels,
    _to_braille,
)


class TestBrailleEncoder:
    def test_full_cell_maps_to_braille_full_block(self):
        rows = ["##", "##", "##", "##"]

        assert _to_braille(rows) == [chr(0x28FF)]

    def test_empty_cell_maps_to_braille_blank(self):
        rows = ["..", "..", "..", ".."]

        assert _to_braille(rows) == [chr(0x2800)]


class TestLedFrame:
    def test_all_states_render_fixed_screen_size(self):
        for state in ("idle", "opening", "running", "agent", "success", "error"):
            frame = _render_led_frame(state, tick=3)

            assert len(frame) == 3
            assert all(len(row) == 20 for row in frame)
            assert any(char != chr(0x2800) for row in frame for char in row)

    def test_unknown_state_falls_back_to_idle(self):
        assert _render_led_frame("missing", tick=2) == _render_led_frame("idle", tick=2)

    def test_marquee_moves_between_ticks(self):
        assert _render_led_frame("idle", tick=0) != _render_led_frame("idle", tick=4)

    def test_text_pixels_uses_question_mark_for_unknown_chars(self):
        rows = _text_pixels("@")

        assert len(rows) == 5
        assert all(len(row) == 4 for row in rows)
        assert any("#" in row for row in rows)

    def test_colorize_applies_per_cell_palette(self):
        art = _colorize_braille(["abc"], "cyan", tick=0)

        assert "[bold #00d4ff]a[/]" in art
        assert "[bold #00fff0]b[/]" in art
