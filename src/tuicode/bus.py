from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Callable, Type, TypeVar

from tuicode.events import Event

E = TypeVar("E", bound=Event)
Handler = Callable[[Event], None]


class EventBus:
    """轻量级同步事件总线。

    subscribe() 返回 unsubscribe callable，调用后移除该订阅。
    publish() 按注册顺序同步调用订阅方；async handler 通过 asyncio.create_task 调度。
    """

    def __init__(self) -> None:
        self._handlers: dict[type[Event], list[Handler]] = defaultdict(list)

    def subscribe(
        self, event_type: Type[E], handler: Callable[[E], None]
    ) -> Callable[[], None]:
        """注册订阅，返回取消订阅的 callable。"""
        self._handlers[event_type].append(handler)  # type: ignore[arg-type]

        def unsubscribe() -> None:
            try:
                self._handlers[event_type].remove(handler)  # type: ignore[arg-type]
            except ValueError:
                pass

        return unsubscribe

    def publish(self, event: Event) -> None:
        """发布事件，按注册顺序通知所有订阅方。"""
        for handler in list(self._handlers[type(event)]):
            if asyncio.iscoroutinefunction(handler):
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(handler(event))  # type: ignore[arg-type]
                except RuntimeError:
                    asyncio.run(handler(event))  # type: ignore[arg-type]
            else:
                handler(event)  # type: ignore[arg-type]


# 模块级默认总线实例，供各模块直接导入使用
default_bus: EventBus = EventBus()
