from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database.session import get_db_session
from app.database.models import Conversation, Message
from app.security.dependencies import get_current_user
from app.agent.orchestrator import AgentOrchestrator, AgentContext
from app.models.providers import Message as LLMMessage
from app.main import agent_orchestrator, memory_manager


router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    stream: bool = False


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    tool_calls: Optional[List[dict]] = None


class ConversationCreate(BaseModel):
    title: str
    system_prompt: Optional[str] = None


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    is_archived: bool


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    if not agent_orchestrator:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    if request.conversation_id:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == request.conversation_id,
                Conversation.user_id == current_user.id,
            )
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = await memory_manager.create_conversation(
            db, current_user.id, "New Conversation"
        )
    
    history = await memory_manager.get_conversation_context(db, conversation.id)
    llm_messages = [
        LLMMessage(role=m.role, content=m.content, tool_calls=m.tool_calls, tool_call_id=m.tool_call_id)
        for m in history
    ]
    
    context = AgentContext(user_id=current_user.id, conversation_id=conversation.id)
    
    response = await agent_orchestrator.chat(
        request.message, context, llm_messages, stream=False
    )
    
    await memory_manager.save_conversation_message(
        db, conversation.id, "user", request.message
    )
    
    await memory_manager.save_conversation_message(
        db, conversation.id, "assistant", response.content or "", response.tool_calls
    )
    
    conversation.updated_at = datetime.utcnow()
    await db.commit()
    
    return ChatResponse(
        response=response.content or "",
        conversation_id=conversation.id,
        tool_calls=response.tool_calls,
    )


@router.post("/conversations", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    request: ConversationCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    conversation = await memory_manager.create_conversation(
        db, current_user.id, request.title, request.system_prompt
    )
    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at.isoformat(),
        updated_at=conversation.updated_at.isoformat(),
        is_archived=conversation.is_archived,
    )


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    limit: int = 50,
):
    conversations = await memory_manager.get_user_conversations(db, current_user.id, limit=limit)
    return [
        ConversationResponse(
            id=c.id,
            title=c.title,
            created_at=c.created_at.isoformat(),
            updated_at=c.updated_at.isoformat(),
            is_archived=c.is_archived,
        )
        for c in conversations
    ]


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = await memory_manager.get_conversation_context(db, conversation_id, limit=100)
    
    return {
        "id": conversation.id,
        "title": conversation.title,
        "system_prompt": conversation.system_prompt,
        "model_provider": conversation.model_provider,
        "model_name": conversation.model_name,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
        "is_archived": conversation.is_archived,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "tool_calls": m.tool_calls,
                "tool_call_id": m.tool_call_id,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    await db.delete(conversation)
    await db.commit()
    return {"message": "Conversation deleted"}


from datetime import datetime