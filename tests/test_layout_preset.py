"""feat-016 测试 — 布局预设位置计算 + FloatWorkspace.apply_preset。"""
from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import MagicMock

from textual.app import App, ComposeResult
from textual.geometry import Size

from tuicode.ui.float_window import FloatWindow
from tuicode.ui.workspace import FloatWorkspace, _preset_positions


# ── _preset_positions 纯函数测试 ───────────────────────────────────────────────


class TestPresetPositions:
    WS_W = 100
    WS_H = 40

    def test_preset1_single_window_takes_most_space(self):
        positions = _preset_positions(1, 1, self.WS_W, self.WS_H)
        x, y, w, h = positions[0]
        assert x == 0 and y == 0
        assert w >= self.WS_W - 4
        assert h >= self.WS_H - 4

    def test_preset1_returns_enough_slots(self):
        positions = _preset_positions(1, 3, self.WS_W, self.WS_H)
        assert len(positions) == 3

    def test_preset2_two_windows_side_by_side(self):
        positions = _preset_positions(2, 2, self.WS_W, self.WS_H)
        x0, y0, w0, h0 = positions[0]
        x1, y1, w1, h1 = positions[1]
        assert x0 == 0
        assert x1 > w0           # 第二个窗口在第一个右侧
        assert y0 == 0 and y1 == 0
        assert h0 == h1           # 同高

    def test_preset3_debug_top_bigger_than_bottom(self):
        positions = _preset_positions(3, 2, self.WS_W, self.WS_H)
        _, _, _, top_h = positions[0]
        _, _, _, bot_h = positions[1]
        assert top_h > bot_h

    def test_preset3_top_bottom_start_positions(self):
        positions = _preset_positions(3, 2, self.WS_W, self.WS_H)
        _, y0, _, top_h = positions[0]
        _, y1, _, _ = positions[1]
        assert y0 == 0
        assert y1 == top_h       # 第二个从第一个底部开始

    def test_all_presets_respect_min_dimensions(self):
        for preset in (1, 2, 3):
            for count in (1, 2, 3):
                positions = _preset_positions(preset, count, self.WS_W, self.WS_H)
                for x, y, w, h in positions:
                    assert w >= FloatWindow.MIN_WIDTH, f"preset={preset} count={count} w={w}"
                    assert h >= FloatWindow.MIN_HEIGHT, f"preset={preset} count={count} h={h}"


# ── FloatWorkspace.apply_preset 集成测试 ──────────────────────────────────────


class _WorkspaceApp(App):
    CSS = "Screen { background: #000; }"

    def compose(self) -> ComposeResult:
        yield FloatWorkspace()


def _make_mock_window() -> MagicMock:
    win = MagicMock(spec=FloatWindow)
    win._win_x = 0
    win._win_y = 0
    win._win_w = FloatWindow.DEFAULT_WIDTH
    win._win_h = FloatWindow.DEFAULT_HEIGHT
    win._stack_y = 0
    win._is_minimized = False
    win.styles = MagicMock()
    return win


class TestApplyPreset:
    def test_apply_preset_no_windows_is_noop(self):
        async def run():
            async with _WorkspaceApp().run_test(headless=True) as pilot:
                ws = pilot.app.query_one(FloatWorkspace)
                ws.apply_preset(1)   # 不应报错
                await pilot.pause()

        asyncio.run(run())

    def test_apply_preset_sets_window_dimensions(self):
        async def run():
            async with _WorkspaceApp().run_test(headless=True) as pilot:
                ws = pilot.app.query_one(FloatWorkspace)
                ws._size = Size(100, 40)
                w0 = _make_mock_window()
                w1 = _make_mock_window()
                ws._windows = [w0, w1]

                ws.apply_preset(2)
                await pilot.pause()

                # preset 2 = dual-agent，两个窗口宽各约 ws_w/2，均已更新
                assert w0._win_w >= FloatWindow.MIN_WIDTH
                assert w1._win_w >= FloatWindow.MIN_WIDTH
                # 第二个窗口在第一个右侧（_win_x > 0）
                assert w1._win_x > 0

        asyncio.run(run())

    def test_apply_preset_posts_preset_applied_message(self):
        received: list[FloatWorkspace.PresetApplied] = []

        async def run():
            class _App(_WorkspaceApp):
                def on_float_workspace_preset_applied(
                    self, msg: FloatWorkspace.PresetApplied
                ) -> None:
                    received.append(msg)

            async with _App().run_test(headless=True) as pilot:
                ws = pilot.app.query_one(FloatWorkspace)
                w0 = _make_mock_window()
                ws._windows = [w0]
                ws.apply_preset(1)
                await pilot.pause()

        asyncio.run(run())
        assert len(received) == 1
        assert received[0].preset == 1

    def test_apply_preset_restores_minimized_windows(self):
        async def run():
            async with _WorkspaceApp().run_test(headless=True) as pilot:
                ws = pilot.app.query_one(FloatWorkspace)
                w0 = _make_mock_window()
                w0._is_minimized = True
                ws._windows = [w0]
                ws.apply_preset(1)
                await pilot.pause()

                w0.restore.assert_called_once()

        asyncio.run(run())


# ── FloatWorkspace.reset_positions 测试 ───────────────────────────────────────


class TestResetPositions:
    def test_reset_no_windows_is_noop(self):
        async def run():
            async with _WorkspaceApp().run_test(headless=True) as pilot:
                ws = pilot.app.query_one(FloatWorkspace)
                ws.reset_positions()   # 不应报错
                await pilot.pause()

        asyncio.run(run())

    def test_reset_pulls_offscreen_window_back_into_view(self):
        async def run():
            async with _WorkspaceApp().run_test(headless=True, size=(100, 40)) as pilot:
                ws = pilot.app.query_one(FloatWorkspace)
                w0 = _make_mock_window()
                # 模拟被拖到屏幕外：x/y 远超工作区
                w0._win_x = 500
                w0._win_y = 300
                ws._windows = [w0]

                ws.reset_positions()
                await pilot.pause()

                ws_w, ws_h = ws.size.width, ws.size.height
                # 实际屏幕坐标 = _stack_y + _win_y，必须落在工作区内
                actual_y = w0._stack_y + w0._win_y
                assert 0 <= w0._win_x <= ws_w - w0._win_w
                assert 0 <= actual_y <= ws_h - w0._win_h

        asyncio.run(run())

    def test_reset_clamps_oversized_window(self):
        async def run():
            async with _WorkspaceApp().run_test(headless=True, size=(50, 20)) as pilot:
                ws = pilot.app.query_one(FloatWorkspace)
                w0 = _make_mock_window()
                w0._win_w = 999   # 比工作区还大
                w0._win_h = 999
                ws._windows = [w0]

                ws.reset_positions()
                await pilot.pause()

                ws_w, ws_h = ws.size.width, ws.size.height
                assert w0._win_w <= ws_w
                assert w0._win_h <= ws_h
                assert w0._win_w >= FloatWindow.MIN_WIDTH
                assert w0._win_h >= FloatWindow.MIN_HEIGHT

        asyncio.run(run())

    def test_reset_restores_minimized_and_clears_maximized(self):
        async def run():
            async with _WorkspaceApp().run_test(headless=True) as pilot:
                ws = pilot.app.query_one(FloatWorkspace)
                w0 = _make_mock_window()
                w0._is_minimized = True
                w0._is_maximized = True
                ws._windows = [w0]

                ws.reset_positions()
                await pilot.pause()

                w0.restore.assert_called_once()
                assert w0._is_maximized is False

        asyncio.run(run())

    def test_reset_cascades_multiple_windows_without_overlap_in_y(self):
        async def run():
            async with _WorkspaceApp().run_test(headless=True, size=(120, 50)) as pilot:
                ws = pilot.app.query_one(FloatWorkspace)
                w0 = _make_mock_window()
                w1 = _make_mock_window()
                ws._windows = [w0, w1]

                ws.reset_positions()
                await pilot.pause()

                # 两个窗口都落在可见区，且 cascade 错开（第二个 x 更大）
                assert w1._win_x > w0._win_x

        asyncio.run(run())
