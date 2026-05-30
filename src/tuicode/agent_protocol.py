"""AgentAdapter Protocol — 所有 AI 智能体适配器必须实现此接口。"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import AsyncIterator, Protocol, runtime_checkable


# ── 支撑数据类型 ──────────────────────────────────────────────────────────────

@dataclass
class AgentCapabilities:
    """适配器声明它支持哪些能力。"""
    streaming: bool = True
    tool_use: bool = True
    multi_turn: bool = True


@dataclass
class Context:
    """发送给智能体的上下文快照。"""
    active_file: Path | None = None
    selection_text: str = ""
    git_status: str = ""
    recent_diffs: list[str] = field(default_factory=list)
    extra: dict = field(default_factory=dict)


@dataclass
class Session:
    """一次智能体会话的句柄。"""
    session_id: str
    agent_id: str


@dataclass
class Chunk:
    """流式响应的一个数据块。"""
    text: str = ""
    is_tool_call: bool = False
    tool_name: str = ""
    tool_args: dict = field(default_factory=dict)
    call_id: str = ""
    is_done: bool = False


@dataclass
class ToolCall:
    """智能体发起的工具调用。"""
    call_id: str
    tool_name: str
    args: dict = field(default_factory=dict)


@dataclass
class ToolResult:
    """工具调用的执行结果。"""
    call_id: str
    approved: bool
    output: str = ""
    error: str = ""


# ── Protocol 定义 ─────────────────────────────────────────────────────────────

@runtime_checkable
class AgentAdapter(Protocol):
    """所有 AI 智能体适配器实现此协议。

    新增适配器时：
    1. 实现所有方法
    2. 在 AgentCapabilities 中声明能力
    3. 不修改宿主层（TuiCode 不依赖具体适配器类）
    """

    agent_id: str
    display_name: str
    capabilities: AgentCapabilities

    async def start_session(self, ctx: Context) -> Session:
        """启动一个新的会话，返回会话句柄。"""
        ...

    async def send_message(self, session: Session, content: str) -> None:
        """向会话发送一条用户消息。"""
        ...

    async def stream_response(self, session: Session) -> AsyncIterator[Chunk]:
        """异步迭代器：流式拉取智能体的响应块。"""
        ...

    async def handle_tool_call(self, call: ToolCall) -> ToolResult:
        """将工具调用结果回传给智能体（由审批 UI 触发）。"""
        ...

    async def stop_session(self, session: Session) -> None:
        """关闭会话，释放资源。"""
        ...
