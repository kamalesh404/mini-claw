from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4
import asyncio


@dataclass
class Event:
    id: str = ""
    event_type: str = ""
    source: str = ""
    payload: Dict[str, Any] = None
    user_id: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())
        if self.payload is None:
            self.payload = {}
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._global_subscribers: List[Callable] = []
    
    def subscribe(self, event_type: str, handler: Callable) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
    
    def subscribe_all(self, handler: Callable) -> None:
        self._global_subscribers.append(handler)
    
    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(handler)
    
    async def emit(self, event: Event) -> None:
        handlers = self._subscribers.get(event.event_type, []) + self._global_subscribers
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception:
                pass
    
    async def emit_raw(
        self,
        event_type: str,
        source: str,
        payload: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> None:
        event = Event(
            event_type=event_type,
            source=source,
            payload=payload,
            user_id=user_id,
        )
        await self.emit(event)


event_bus = EventBus()


EVENT_TYPES = {
    "agent.task.created",
    "agent.task.started",
    "agent.task.completed",
    "agent.task.failed",
    "agent.approval.required",
    "agent.approval.accepted",
    "agent.approval.rejected",
    "github.issue.created",
    "github.issue.updated",
    "github.pull_request.created",
    "github.pull_request.updated",
    "github.workflow.failed",
    "github.workflow.completed",
    "system.low_disk",
    "system.high_cpu",
    "system.high_gpu",
    "system.agent_started",
    "system.agent_stopped",
}