from __future__ import annotations

from pathlib import Path

from tuicode.agent_memory import (
    AgentSessionRecord,
    AgentSessionStore,
    _extract_osc_title,
    session_brief,
    session_detail,
    strip_terminal_output,
)


def test_store_persists_session_and_transcript(tmp_path: Path):
    store = AgentSessionStore(project_root=tmp_path / "repo", data_home=tmp_path / "data")

    record = store.start_session(
        session_id="abc123ef",
        title="Claude Code",
        agent_type="claude",
        command="claude",
    )
    store.append_output("abc123ef", "\x1b[32mchanged src/app.py\x1b[0m\r\n")
    store.finish_session("abc123ef", status="ended")

    loaded = AgentSessionStore(
        project_root=tmp_path / "repo",
        data_home=tmp_path / "data",
    ).get("abc123ef")

    assert loaded is not None
    assert loaded.session_id == record.session_id
    assert loaded.status == "ended"
    assert "changed src/app.py" in loaded.last_output
    assert "changed src/app.py" in Path(loaded.transcript_path).read_text()


def test_build_continuation_prompt_is_agent_agnostic(tmp_path: Path):
    store = AgentSessionStore(project_root=tmp_path, data_home=tmp_path / "data")
    store.start_session(
        session_id="feed1234",
        title="Claude Code",
        agent_type="claude",
        command="claude",
    )
    store.append_output("feed1234", "目标：实现会话记忆\n待办：让 Codex 继续\n")
    prompt = store.build_continuation_prompt("feed1234")

    assert "请继续这个 TuiCode 项目的上一轮 agent 会话" in prompt
    assert "上一轮 agent: Claude Code (claude)" in prompt
    assert "让 Codex 继续" in prompt
    assert "请先检查当前工作区和 Git 状态" in prompt


def test_handoff_notice_is_short_and_points_to_full_context(tmp_path: Path):
    store = AgentSessionStore(project_root=tmp_path, data_home=tmp_path / "data")
    store.start_session(
        session_id="c0ffee12",
        title="Claude Code",
        agent_type="claude",
        command="claude",
    )
    store.append_output("c0ffee12", "line\n" * 300)

    notice = store.build_handoff_notice("c0ffee12")

    assert "\n" not in notice
    assert "完整上下文已保存到" in notice
    assert "c0ffee12.md" in notice
    handoff = store.handoffs_dir / "c0ffee12.md"
    assert handoff.exists()
    assert "最近 transcript 片段" in handoff.read_text()


def test_closed_does_not_overwrite_ended_status(tmp_path: Path):
    store = AgentSessionStore(project_root=tmp_path, data_home=tmp_path / "data")
    store.start_session(
        session_id="deadbeef",
        title="Codex",
        agent_type="codex",
        command="codex",
    )
    store.finish_session("deadbeef", status="ended")
    store.finish_session("deadbeef", status="closed")

    assert store.get("deadbeef").status == "ended"


def test_strip_terminal_output_removes_ansi_and_carriage_returns():
    assert strip_terminal_output("\x1b[31merror\x1b[0m\r\nnext\rline") == (
        "error\nnext\nline"
    )


def test_strip_terminal_output_removes_osc_and_charset_sequences():
    # OSC 窗口标题序列应被完整剥离
    assert strip_terminal_output("\x1b]0;task title\x07hello") == "hello"
    # G0 字符集序列（\x1b(B 是 ASCII 字符集）应被剥离
    assert strip_terminal_output("\x1b(Bhello\x1b(B") == "hello"
    # 混合场景
    raw = "\x1b7\x1b8\x1b]0;补充项目 README\x07some output\x1b[0m"
    result = strip_terminal_output(raw)
    assert "some output" in result
    assert "\x1b" not in result
    assert "补充项目 README" not in result


def test_extract_osc_title_finds_task_description():
    # 标准格式：spinner + 任务名
    text = "\x1b]0;⠂ 补充项目 README 和开源协议\x07"
    assert _extract_osc_title(text) == "补充项目 README 和开源协议"

    # 完成状态：✳ + 任务名
    text2 = "\x1b]0;✳ 补充项目 README 和开源协议\x07"
    assert _extract_osc_title(text2) == "补充项目 README 和开源协议"

    # 纯 "Claude Code"（空闲状态）不应返回
    assert _extract_osc_title("\x1b]0;✳ Claude Code\x07") == ""

    # 多个 OSC 标题时取最后一个有意义的
    multi = "\x1b]0;✳ Claude Code\x07\x1b]0;⠂ 修复登录 Bug\x07"
    assert _extract_osc_title(multi) == "修复登录 Bug"


def test_session_brief_uses_osc_title_first():
    # osc_title 直接设置时优先于其他内容
    record = AgentSessionRecord(
        session_id="abc123ef",
        project_root="/tmp/project",
        title="Claude Code",
        agent_type="claude",
        command="claude",
        created_at="2026-05-30T00:00:00+00:00",
        updated_at="2026-05-30T00:01:00+00:00",
        summary="一些其他内容",
        last_output="其他输出",
        osc_title="重构 pty_terminal.py",
    )
    assert session_brief(record) == "重构 pty_terminal.py"


def test_append_output_extracts_osc_title(tmp_path: Path):
    store = AgentSessionStore(project_root=tmp_path / "repo", data_home=tmp_path / "data")
    store.start_session(
        session_id="osc12345",
        title="Claude Code",
        agent_type="claude",
        command="claude",
    )
    # 包含 OSC 标题的 PTY 输出
    store.append_output("osc12345", "\x1b]0;✳ 实现用户认证模块\x07some output\n")

    record = store.get("osc12345")
    assert record is not None
    assert record.osc_title == "实现用户认证模块"
    assert session_brief(record) == "实现用户认证模块"


def test_finish_session_with_pyte_scrollback(tmp_path: Path):
    store = AgentSessionStore(project_root=tmp_path / "repo", data_home=tmp_path / "data")
    store.start_session(
        session_id="pyte1234",
        title="Claude Code",
        agent_type="claude",
        command="claude",
        )
    store.append_output("pyte1234", "\x1b]0;⠂ 修复文件树排序\x07\n")

    scrollback = "修复文件树排序问题\n已更新 file_tree.py\n排序逻辑优化完成"
    store.finish_session("pyte1234", status="ended", scrollback_text=scrollback)

    record = store.get("pyte1234")
    assert record is not None
    assert record.status == "ended"
    assert "修复文件树排序" in record.summary
    assert "已更新 file_tree.py" in record.summary


def test_session_brief_prefers_meaningful_content():
    record = AgentSessionRecord(
        session_id="abc123ef",
        project_root="/tmp/project",
        title="Claude Code",
        agent_type="claude",
        command="claude",
        created_at="2026-05-30T00:00:00+00:00",
        updated_at="2026-05-30T00:01:00+00:00",
        summary="记录了 Claude Code 的 PTY 会话输出；\n目标：实现会话详情预览",
        last_output="普通输出",
    )

    assert session_brief(record) == "目标：实现会话详情预览"


def test_session_brief_filters_terminal_ui_noise():
    record = AgentSessionRecord(
        session_id="abc123ef",
        project_root="/tmp/project",
        title="Claude Code",
        agent_type="claude",
        command="claude",
        created_at="2026-05-30T00:00:00+00:00",
        updated_at="2026-05-30T00:01:00+00:00",
        summary="",
        last_output=(
            "▶▶bypasspermissionson (shift+tabtocycle) foragents\n"
            "Sonnet4.6withhigheffort ClaudePro\n"
            "目标：继续优化历史会话展示\n"
        ),
    )

    assert session_brief(record) == "目标：继续优化历史会话展示"


def test_session_detail_contains_review_context():
    record = AgentSessionRecord(
        session_id="abc123ef",
        project_root="/tmp/project",
        title="Codex",
        agent_type="codex",
        command="codex",
        created_at="2026-05-30T00:00:00+00:00",
        updated_at="2026-05-30T00:01:00+00:00",
        status="ended",
        transcript_path="/tmp/transcript.txt",
        summary="摘要内容",
        last_output="最近输出",
    )

    detail = session_detail(record)
    assert "Codex · codex · ended" in detail
    assert "摘要内容" in detail
    assert "最近输出" in detail
    assert "/tmp/transcript.txt" in detail


def test_session_detail_omits_noisy_terminal_chrome():
    record = AgentSessionRecord(
        session_id="abc123ef",
        project_root="/tmp/project",
        title="Claude Code",
        agent_type="claude",
        command="claude --dangerously-skip-permissions",
        created_at="2026-05-30T00:00:00+00:00",
        updated_at="2026-05-30T00:01:00+00:00",
        status="closed",
        summary="记录了 Claude Code 的 PTY 会话输出；\n任务：整理会话列表",
        last_output=(
            "▶▶bypasspermissionson (shift+tabtocycle) foragents\n"
            "ClaudeCodev2.1.158\n"
            "修复：列表标题不再混乱\n"
        ),
    )

    detail = session_detail(record)
    assert "bypasspermissions" not in detail
    assert "ClaudeCodev" not in detail
    assert "任务：整理会话列表" in detail
    assert "修复：列表标题不再混乱" in detail
