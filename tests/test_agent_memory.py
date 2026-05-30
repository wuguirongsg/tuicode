from __future__ import annotations

from pathlib import Path

from tuicode.agent_memory import AgentSessionStore, strip_terminal_output


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
