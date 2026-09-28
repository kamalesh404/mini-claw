from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Dict, List, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
import asyncio

from app.database.session import get_db_session
from app.database.models import User, Session as SessionModel
from app.security.auth import verify_token, decode_token
from app.events.bus import event_bus, Event


router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, connection_id: str):
        await websocket.accept()
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(websocket)
        
        if connection_id not in self.active_connections:
            self.active_connections[connection_id] = set()
        self.active_connections[connection_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: str, connection_id: str):
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        if connection_id in self.active_connections:
            self.active_connections[connection_id].discard(websocket)
            if not self.active_connections[connection_id]:
                del self.active_connections[connection_id]
    
    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.user_connections:
            for ws in self.user_connections[user_id].copy():
                try:
                    await ws.send_json(message)
                except Exception:
                    self.user_connections[user_id].discard(ws)
    
    async def broadcast(self, message: dict):
        for connections in self.user_connections.values():
            for ws in connections.copy():
                try:
                    await ws.send_json(message)
                except Exception:
                    connections.discard(ws)


manager = ConnectionManager()


async def get_user_from_token(token: str, db: AsyncSession) -> User | None:
    user_id = verify_token(token, "access")
    if not user_id:
        return None
    
    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    return result.scalar_one_or_none()


@router.websocket("/agent")
async def websocket_agent(
    websocket: WebSocket,
    token: str = Query(...),
):
    connection_id = f"agent_{id(websocket)}"
    db_gen = get_db_session()
    db = await db_gen.__anext__()
    
    try:
        user = await get_user_from_token(token, db)
        if not user:
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        await manager.connect(websocket, user.id, connection_id)
        
        await websocket.send_json({
            "type": "connected",
            "user_id": user.id,
            "connection_id": connection_id,
        })
        
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif data.get("type") == "chat":
                from app.main import agent_orchestrator, memory_manager
                
                if agent_orchestrator:
                    from app.agent.orchestrator import AgentContext
                    from app.models.providers import Message as LLMMessage
                    
                    conversation_id = data.get("conversation_id")
                    message = data.get("message")
                    
                    if conversation_id:
                        history = await memory_manager.get_conversation_context(db, conversation_id)
                    else:
                        history = []
                    
                    llm_messages = [
                        LLMMessage(role=m.role, content=m.content, tool_calls=m.tool_calls, tool_call_id=m.tool_call_id)
                        for m in history
                    ]
                    
                    context = AgentContext(user_id=user.id, conversation_id=conversation_id)
                    
                    async for chunk in agent_orchestrator.chat(message, context, llm_messages, stream=True):
                        await websocket.send_json({
                            "type": "chat_chunk",
                            "content": chunk.content,
                            "tool_calls": chunk.tool_calls,
                            "finish_reason": chunk.finish_reason,
                        })
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
    finally:
        manager.disconnect(websocket, user.id if user else "unknown", connection_id)
        await db_gen.aclose()


@router.websocket("/tasks")
async def websocket_tasks(
    websocket: WebSocket,
    token: str = Query(...),
):
    connection_id = f"tasks_{id(websocket)}"
    db_gen = get_db_session()
    db = await db_gen.__anext__()
    
    try:
        user = await get_user_from_token(token, db)
        if not user:
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        await manager.connect(websocket, user.id, connection_id)
        
        async def task_event_handler(event: Event):
            await websocket.send_json({
                "type": "task_event",
                "event_type": event.event_type,
                "payload": event.payload,
            })
        
        event_bus.subscribe("agent.task.started", task_event_handler)
        event_bus.subscribe("agent.task.completed", task_event_handler)
        event_bus.subscribe("agent.task.failed", task_event_handler)
        event_bus.subscribe("agent.approval.required", task_event_handler)
        
        try:
            while True:
                await websocket.receive_json()
        except WebSocketDisconnect:
            pass
        finally:
            event_bus.unsubscribe("agent.task.started", task_event_handler)
            event_bus.unsubscribe("agent.task.completed", task_event_handler)
            event_bus.unsubscribe("agent.task.failed", task_event_handler)
            event_bus.unsubscribe("agent.approval.required", task_event_handler)
    
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
    finally:
        manager.disconnect(websocket, user.id if user else "unknown", connection_id)
        await db_gen.aclose()


@router.websocket("/events")
async def websocket_events(
    websocket: WebSocket,
    token: str = Query(...),
):
    connection_id = f"events_{id(websocket)}"
    db_gen = get_db_session()
    db = await db_gen.__anext__()
    
    try:
        user = await get_user_from_token(token, db)
        if not user:
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        await manager.connect(websocket, user.id, connection_id)
        
        async def event_handler(event: Event):
            if event.user_id is None or event.user_id == user.id:
                await websocket.send_json({
                    "type": "event",
                    "event_type": event.event_type,
                    "source": event.source,
                    "payload": event.payload,
                    "timestamp": event.timestamp.isoformat(),
                })
        
        event_bus.subscribe_all(event_handler)
        
        try:
            while True:
                await websocket.receive_json()
        except WebSocketDisconnect:
            pass
        finally:
            event_bus.unsubscribe(event_handler)
    
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
    finally:
        manager.disconnect(websocket, user.id if user else "unknown", connection_id)
        await db_gen.aclose()


@router.websocket("/pc")
async def websocket_pc_status(
    websocket: WebSocket,
    token: str = Query(...),
    interval: int = Query(5, ge=1, le=60),
):
    connection_id = f"pc_{id(websocket)}"
    db_gen = get_db_session()
    db = await db_gen.__anext__()
    
    try:
        user = await get_user_from_token(token, db)
        if not user:
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        await manager.connect(websocket, user.id, connection_id)
        
        from app.main import tool_registry
        from app.security.dependencies import get_user_permissions
        
        user_permissions = get_user_permissions(user)
        
        while True:
            tools = [
                "get_cpu_usage", "get_gpu_usage", "get_ram_usage", 
                "get_disk_usage", "get_battery_status",
            ]
            
            pc_data = {}
            for tool_name in tools:
                if hasattr(tool_registry, '_tools') and tool_name in tool_registry._tools:
                    output = await tool_registry.execute_tool(tool_name, {}, user_permissions)
                    if output.success:
                        pc_data[tool_name] = output.data
            
            await websocket.send_json({
                "type": "pc_status",
                "data": pc_data,
            })
            
            await asyncio.sleep(interval)
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
    finally:
        manager.disconnect(websocket, user.id if user else "unknown", connection_id)
        await db_gen.aclose()