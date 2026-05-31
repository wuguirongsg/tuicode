"""TerminalStrip 多终端 Tab 测试。"""
from __future__ import annotations

import asyncio

import pytest
from textual.app import App, ComposeResult

from tuicode.ui.pty_terminal import PtyTerminal
from tuicode.ui.terminal_strip import TerminalStrip


class _StripApp(App):
    def compose(self) -> ComposeResult:
        yield TerminalStrip()


def test_terminal_strip_starts_with_one_tab():
    async def run():
        app = _StripApp()
        async with app.run_test(size=(80, 24)) as pilot:
            strip = app.query_one(TerminalStrip)
            assert len(strip._tabs) == 1
            assert strip.active_terminal is not None
    asyncio.run(run())


def test_terminal_strip_add_tab_on_plus_click():
    async def run():
        app = _StripApp()
        async with app.run_test(size=(80, 24)) as pilot:
            strip = app.query_one(TerminalStrip)
            await pilot.click("#ts-add")
            await asyncio.sleep(0.1)
            assert len(strip._tabs) == 2
            terms = app.query(PtyTerminal)
            assert len(terms) == 2
    asyncio.run(run())


def test_terminal_strip_switch_tab():
    async def run():
        app = _StripApp()
        async with app.run_test(size=(80, 24)) as pilot:
            strip = app.query_one(TerminalStrip)
            await pilot.click("#ts-add")
            await asyncio.sleep(0.1)
            first_id = strip._tabs[0].tab_id
            second_id = strip._tabs[1].tab_id
            await pilot.click(f"#ts-tab-{first_id}")
            assert strip._active_tab_id == first_id
            term1 = app.query_one(f"#ts-term-{first_id}", PtyTerminal)
            term2 = app.query_one(f"#ts-term-{second_id}", PtyTerminal)
            assert term1.display is True
            assert term2.display is False
    asyncio.run(run())
