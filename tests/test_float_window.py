"""feat-003 单元测试 — FloatWindow 浮窗基类 + FloatWorkspace 管理器。"""
from __future__ import annotations

import asyncio

from textual.app import App, ComposeResult

from tuicode.ui.float_window import FloatWindow, ResizeHandle, TitleBar
from tuicode.ui.workspace import FloatWorkspace


# ── 测试 App 骨架 ─────────────────────────────────────────────────────────────


class WorkspaceApp(App):
    CSS = "Screen { background: #0d1117; }"

    def compose(self) -> ComposeResult:
        yield FloatWorkspace()


# ── TitleBar 单元测试 ─────────────────────────────────────────────────────────


class TestTitleBar:
    def test_titlebar_composes_buttons_and_title(self):
        async def run():
            app = App()
            async with app.run_test(headless=True) as pilot:
                await app.mount(TitleBar("My Window"))
                await pilot.pause()
                assert app.query_one("#btn-close")
                assert app.query_one("#btn-min")
                assert app.query_one("#btn-max")
                assert app.query_one("#win-title")

        asyncio.run(run())

    def test_drag_moved_message_bubbles_to_parent(self):
        received: list[TitleBar.DragMoved] = []

        async def run():
            class _App(App):
                def compose(self) -> ComposeResult:
                    yield TitleBar("test")

                def on_title_bar_drag_moved(self, msg: TitleBar.DragMoved) -> None:
                    received.append(msg)

            async with _App().run_test(headless=True) as pilot:
                tb = pilot.app.query_one(TitleBar)
                tb.post_message(TitleBar.DragMoved(5, 3))
                await pilot.pause()

        asyncio.run(run())
        assert len(received) == 1
        assert received[0].dx == 5
        assert received[0].dy == 3


# ── FloatWindow 单元测试 ──────────────────────────────────────────────────────


class TestFloatWindow:
    def test_window_mounts_with_title(self):
        async def run():
            class _App(App):
                def compose(self) -> ComposeResult:
                    yield FloatWindow("编辑器")

            async with _App().run_test(headless=True) as pilot:
                await pilot.pause()
                tb = pilot.app.query_one(TitleBar)
                title_text = tb.query_one("#win-title").render()
                assert "编辑器" in str(title_text)

        asyncio.run(run())

    def test_initial_position_applied_on_mount(self):
        async def run():
            class _App(App):
                def compose(self) -> ComposeResult:
                    yield FloatWindow("Test", x=10, y=3)

            async with _App().run_test(headless=True) as pilot:
                await pilot.pause()
                win = pilot.app.query_one(FloatWindow)
                assert win._win_x == 10
                assert win._win_y == 3

        asyncio.run(run())

    def test_close_button_removes_window(self):
        async def run():
            class _App(App):
                def compose(self) -> ComposeResult:
                    yield FloatWindow("关闭测试")

            async with _App().run_test(headless=True) as pilot:
                await pilot.pause()
                assert len(pilot.app.query(FloatWindow)) == 1
                await pilot.click("#btn-close")
                await pilot.pause()
                assert len(pilot.app.query(FloatWindow)) == 0

        asyncio.run(run())

    def test_close_posts_closed_message(self):
        received: list[FloatWindow.Closed] = []

        async def run():
            class _App(App):
                def compose(self) -> ComposeResult:
                    yield FloatWindow("msg 测试")

                def on_float_window_closed(self, msg: FloatWindow.Closed) -> None:
                    received.append(msg)

            async with _App().run_test(headless=True) as pilot:
                await pilot.pause()
                await pilot.click("#btn-close")
                await pilot.pause()

        asyncio.run(run())
        assert len(received) == 1
        assert isinstance(received[0].window, FloatWindow)

    def test_minimize_hides_body(self):
        async def run():
            class _App(App):
                def compose(self) -> ComposeResult:
                    yield FloatWindow("最小化测试")

            async with _App().run_test(headless=True) as pilot:
                await pilot.pause()
                win = pilot.app.query_one(FloatWindow)
                body = win.query_one("#win-body")
                assert body.display is True

                await pilot.click("#btn-min")
                await pilot.pause()
                assert win._is_minimized is True
                assert body.display is False

                # 再次点击还原
                await pilot.click("#btn-min")
                await pilot.pause()
                assert win._is_minimized is False
                assert body.display is True

        asyncio.run(run())

    def test_maximize_and_restore(self):
        async def run():
            class _App(App):
                def compose(self) -> ComposeResult:
                    yield FloatWindow("最大化测试", x=5, y=2)

            async with _App().run_test(headless=True) as pilot:
                await pilot.pause()
                win = pilot.app.query_one(FloatWindow)
                assert win._is_maximized is False

                await pilot.click("#btn-max")
                await pilot.pause()
                assert win._is_maximized is True
                assert win._win_x == 0
                assert win._win_y == 0

                # 还原
                await pilot.click("#btn-max")
                await pilot.pause()
                assert win._is_maximized is False
                assert win._win_x == 5
                assert win._win_y == 2

        asyncio.run(run())

    def test_drag_moves_window_position(self):
        async def run():
            class _App(App):
                def compose(self) -> ComposeResult:
                    yield FloatWindow("拖动测试", x=0, y=0)

            async with _App().run_test(headless=True) as pilot:
                await pilot.pause()
                win = pilot.app.query_one(FloatWindow)
                original_x = win._win_x

                # 手动发送 DragMoved 消息模拟拖动
                tb = win.query_one(TitleBar)
                tb.post_message(TitleBar.DragMoved(5, 3))
                await pilot.pause()

                assert win._win_x == original_x + 5
                assert win._win_y == 3

        asyncio.run(run())

    def test_resize_updates_dimensions(self):
        async def run():
            class _App(App):
                def compose(self) -> ComposeResult:
                    yield FloatWindow("缩放测试")

            async with _App().run_test(headless=True) as pilot:
                await pilot.pause()
                win = pilot.app.query_one(FloatWindow)
                orig_w = win._win_w
                orig_h = win._win_h

                # 手动发送 Resized 消息
                rh = win.query_one(ResizeHandle)
                rh.post_message(ResizeHandle.Resized(10, 5))
                await pilot.pause()

                assert win._win_w == orig_w + 10
                assert win._win_h == orig_h + 5

        asyncio.run(run())

    def test_resize_respects_minimum_size(self):
        async def run():
            class _App(App):
                def compose(self) -> ComposeResult:
                    yield FloatWindow("最小尺寸测试")

            async with _App().run_test(headless=True) as pilot:
                await pilot.pause()
                win = pilot.app.query_one(FloatWindow)

                rh = win.query_one(ResizeHandle)
                rh.post_message(ResizeHandle.Resized(-9999, -9999))
                await pilot.pause()

                assert win._win_w >= FloatWindow.MIN_WIDTH
                assert win._win_h >= FloatWindow.MIN_HEIGHT

        asyncio.run(run())


# ── FloatWorkspace 测试 ───────────────────────────────────────────────────────


class TestFloatWorkspace:
    def test_open_three_windows(self):
        async def run():
            async with WorkspaceApp().run_test(headless=True) as pilot:
                ws = pilot.app.query_one(FloatWorkspace)
                await ws.open_window(FloatWindow("Win 1"))
                await ws.open_window(FloatWindow("Win 2"))
                await ws.open_window(FloatWindow("Win 3"))
                await pilot.pause()
                assert len(ws._windows) == 3
                assert len(pilot.app.query(FloatWindow)) == 3

        asyncio.run(run())

    def test_hint_hides_when_window_opens(self):
        async def run():
            async with WorkspaceApp().run_test(headless=True) as pilot:
                ws = pilot.app.query_one(FloatWorkspace)
                hint = ws.query_one("#ws-hint")
                assert hint.display is True

                await ws.open_window(FloatWindow("first"))
                await pilot.pause()
                assert hint.display is False

        asyncio.run(run())

    def test_hint_shows_when_all_windows_closed(self):
        async def run():
            async with WorkspaceApp().run_test(headless=True) as pilot:
                ws = pilot.app.query_one(FloatWorkspace)
                await ws.open_window(FloatWindow("only"))
                await pilot.pause()
                await pilot.click("#btn-close")
                await pilot.pause()
                assert ws.query_one("#ws-hint").display is True

        asyncio.run(run())

    def test_cascade_positions_are_staggered(self):
        async def run():
            async with WorkspaceApp().run_test(headless=True) as pilot:
                ws = pilot.app.query_one(FloatWorkspace)
                w1 = await ws.open_window(FloatWindow("A"))
                w2 = await ws.open_window(FloatWindow("B"))
                await pilot.pause()
                # _win_y 是 offset 值（含 stack_y 补偿），比较实际渲染区域
                assert w2.region.x > w1.region.x
                assert w2.region.y > w1.region.y

        asyncio.run(run())

    def test_closed_window_removed_from_list(self):
        async def run():
            async with WorkspaceApp().run_test(headless=True) as pilot:
                ws = pilot.app.query_one(FloatWorkspace)
                await ws.open_window(FloatWindow("to-close"))
                await pilot.pause()
                assert len(ws._windows) == 1

                await pilot.click("#btn-close")
                await pilot.pause()
                assert len(ws._windows) == 0

        asyncio.run(run())
