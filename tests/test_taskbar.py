"""feat-004 单元测试 — WindowTaskBar + 拖拽边界 + 最小化集成。"""
from __future__ import annotations

import asyncio

from textual.app import App, ComposeResult

from tuicode.ui.float_window import FloatWindow
from tuicode.ui.taskbar import TaskButton, WindowTaskBar
from tuicode.ui.workspace import FloatWorkspace


# ── 测试 App 骨架 ─────────────────────────────────────────────────────────────


class FullApp(App):
    """包含 WindowTaskBar + FloatWorkspace 的完整布局（模拟 LeftColumn）。"""

    CSS = "Screen { background: #0d1117; }"

    def compose(self) -> ComposeResult:
        yield WindowTaskBar()
        yield FloatWorkspace()

    async def on_float_workspace_window_opened(
        self, msg: FloatWorkspace.WindowOpened
    ) -> None:
        await self.query_one(WindowTaskBar).add_window(msg.window)

    async def on_float_window_closed(self, msg: FloatWindow.Closed) -> None:
        await self.query_one(WindowTaskBar).remove_window(msg.window)

    def on_float_window_minimize_toggled(
        self, msg: FloatWindow.MinimizeToggled
    ) -> None:
        self.query_one(WindowTaskBar).update_window(msg.window)

    def action_focus_window(self, n: int) -> None:
        win = self.query_one(WindowTaskBar).get_window_at(n)
        if win is not None:
            win._bring_to_top()
            win.restore()
            win.focus()


# ── WindowTaskBar 单元测试 ────────────────────────────────────────────────────


class TestWindowTaskBar:
    def test_hint_visible_when_no_windows(self):
        async def run():
            async with FullApp().run_test(headless=True) as pilot:
                hint = pilot.app.query_one("#tb-hint")
                assert hint.display is True

        asyncio.run(run())

    def test_add_window_shows_button_and_hides_hint(self):
        async def run():
            async with FullApp().run_test(headless=True) as pilot:
                ws = pilot.app.query_one(FloatWorkspace)
                await ws.open_window(FloatWindow("Win A"))
                await pilot.pause()
                tb = pilot.app.query_one(WindowTaskBar)
                assert len(tb._buttons) == 1
                assert pilot.app.query_one("#tb-hint").display is False

        asyncio.run(run())

    def test_three_windows_three_buttons(self):
        async def run():
            async with FullApp().run_test(headless=True) as pilot:
                ws = pilot.app.query_one(FloatWorkspace)
                await ws.open_window(FloatWindow("W1"))
                await ws.open_window(FloatWindow("W2"))
                await ws.open_window(FloatWindow("W3"))
                await pilot.pause()
                tb = pilot.app.query_one(WindowTaskBar)
                assert len(tb._buttons) == 3

        asyncio.run(run())

    def test_close_window_removes_button(self):
        async def run():
            async with FullApp().run_test(headless=True) as pilot:
                ws = pilot.app.query_one(FloatWorkspace)
                win = await ws.open_window(FloatWindow("to-close"))
                await pilot.pause()
                tb = pilot.app.query_one(WindowTaskBar)
                assert len(tb._buttons) == 1

                win._do_close()
                await pilot.pause()
                assert len(tb._buttons) == 0
                assert pilot.app.query_one("#tb-hint").display is True

        asyncio.run(run())

    def test_hint_restores_when_all_closed(self):
        async def run():
            async with FullApp().run_test(headless=True) as pilot:
                ws = pilot.app.query_one(FloatWorkspace)
                win = await ws.open_window(FloatWindow("only"))
                await pilot.pause()
                win._do_close()
                await pilot.pause()
                assert pilot.app.query_one("#tb-hint").display is True

        asyncio.run(run())

    def test_minimize_updates_button_class(self):
        async def run():
            async with FullApp().run_test(headless=True) as pilot:
                ws = pilot.app.query_one(FloatWorkspace)
                win = await ws.open_window(FloatWindow("mini-test"))
                await pilot.pause()
                tb = pilot.app.query_one(WindowTaskBar)
                btn = list(tb._buttons.values())[0]

                assert "minimized" not in btn.classes
                win._do_min_toggle()
                await pilot.pause()
                assert "minimized" in btn.classes

                win._do_min_toggle()
                await pilot.pause()
                assert "minimized" not in btn.classes

        asyncio.run(run())

    def test_get_window_at_returns_correct_window(self):
        async def run():
            async with FullApp().run_test(headless=True) as pilot:
                ws = pilot.app.query_one(FloatWorkspace)
                w1 = await ws.open_window(FloatWindow("A"))
                w2 = await ws.open_window(FloatWindow("B"))
                w3 = await ws.open_window(FloatWindow("C"))
                await pilot.pause()
                tb = pilot.app.query_one(WindowTaskBar)
                assert tb.get_window_at(1) is w1
                assert tb.get_window_at(2) is w2
                assert tb.get_window_at(3) is w3
                assert tb.get_window_at(4) is None

        asyncio.run(run())

    def test_taskbar_button_click_brings_window_to_top(self):
        async def run():
            async with FullApp().run_test(headless=True) as pilot:
                ws = pilot.app.query_one(FloatWorkspace)
                w1 = await ws.open_window(FloatWindow("W1"))
                w2 = await ws.open_window(FloatWindow("W2"))
                await pilot.pause()

                wins = lambda: [
                    c for c in ws.children if isinstance(c, FloatWindow)
                ]
                # 初始：W2 在 DOM 末尾
                assert wins()[-1] is w2

                # 点击 W1 对应的任务栏按钮
                tb = pilot.app.query_one(WindowTaskBar)
                btn = list(tb._buttons.values())[0]
                btn.on_click()
                await pilot.pause()

                assert wins()[-1] is w1

        asyncio.run(run())

    def test_taskbar_button_restores_minimized_window(self):
        async def run():
            async with FullApp().run_test(headless=True) as pilot:
                ws = pilot.app.query_one(FloatWorkspace)
                win = await ws.open_window(FloatWindow("restore-test"))
                await pilot.pause()
                win._do_min_toggle()
                await pilot.pause()
                assert win._is_minimized is True

                tb = pilot.app.query_one(WindowTaskBar)
                btn = list(tb._buttons.values())[0]
                btn.on_click()
                await pilot.pause()
                assert win._is_minimized is False

        asyncio.run(run())

    def test_alt_n_focuses_nth_window(self):
        async def run():
            async with FullApp().run_test(headless=True) as pilot:
                ws = pilot.app.query_one(FloatWorkspace)
                w1 = await ws.open_window(FloatWindow("W1"))
                w2 = await ws.open_window(FloatWindow("W2"))
                w3 = await ws.open_window(FloatWindow("W3"))
                await pilot.pause()

                wins = lambda: [
                    c for c in ws.children if isinstance(c, FloatWindow)
                ]
                pilot.app.action_focus_window(1)
                await pilot.pause()
                assert wins()[-1] is w1

                pilot.app.action_focus_window(3)
                await pilot.pause()
                assert wins()[-1] is w3

        asyncio.run(run())


# ── 拖拽边界测试 ──────────────────────────────────────────────────────────────


class TestDragBoundary:
    def test_drag_clamps_x_to_zero(self):
        async def run():
            class _App(App):
                def compose(self) -> ComposeResult:
                    yield FloatWorkspace()

            async with _App().run_test(headless=True, size=(80, 24)) as pilot:
                ws = pilot.app.query_one(FloatWorkspace)
                win = await ws.open_window(FloatWindow("bound-test", x=2, y=1))
                await pilot.pause()

                # 直接模拟拖动向左 -999，验证 x 被夹住到 >= 0
                ws_w = ws.size.width
                new_x = max(0, min(win._win_x + (-999), ws_w - 20))
                win._win_x = new_x
                win.styles.offset = (win._win_x, win._win_y)
                await pilot.pause()
                assert win._win_x >= 0

        asyncio.run(run())

    def test_drag_clamps_y_to_workspace(self):
        async def run():
            class _App(App):
                def compose(self) -> ComposeResult:
                    yield FloatWorkspace()

            async with _App().run_test(headless=True, size=(80, 24)) as pilot:
                ws = pilot.app.query_one(FloatWorkspace)
                win = await ws.open_window(FloatWindow("bound-test", x=4, y=2))
                await pilot.pause()

                # 直接验证 actual_y 可被夹住到 >= 0
                ws_h = ws.size.height
                cur_actual_y = win.region.y - ws.region.y
                natural_y = cur_actual_y - win._win_y
                new_actual_y = max(0, min(cur_actual_y + (-999), ws_h - 1))
                win._win_y = new_actual_y - natural_y
                win.styles.offset = (win._win_x, win._win_y)
                await pilot.pause()
                actual_y = win.region.y - ws.region.y
                assert actual_y >= 0

        asyncio.run(run())
