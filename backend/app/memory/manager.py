from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Memory, Conversation, Message
from app.models.providers import LLMProvider
from app.config import settings


class MemoryManager:
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider
    
    async def add_memory(
        self,
        db: AsyncSession,
        user_id: str,
        category: str,
        key: str,
        value: str,
        metadata: Optional[Dict[str, Any]] = None,
        is_sensitive: bool = False,
    ) -> Memory:
        embedding = None
        if not is_sensitive:
            try:
                embeddings = await self.llm.embed([value])
                embedding = embeddings[0] if embeddings else None
            except Exception:
                pass
        
        memory = Memory(
            id=str(uuid4()),
            user_id=user_id,
            category=category,
            key=key,
            value=value,
            embedding=embedding,
            metadata=metadata or {},
            is_sensitive=is_sensitive,
        )
        db.add(memory)
        await db.flush()
        return memory
    
    async def get_memory(
        self,
        db: AsyncSession,
        user_id: str,
        category: str,
        key: str,
    ) -> Optional[Memory]:
        result = await db.execute(
            select(Memory).where(
                and_(
                    Memory.user_id == user_id,
                    Memory.category == category,
                    Memory.key == key,
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def update_memory(
        self,
        db: AsyncSession,
        user_id: str,
        category: str,
        key: str,
        value: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Memory]:
        memory = await self.get_memory(db, user_id, category, key)
        if not memory:
            return None
        
        memory.value = value
        if metadata:
            memory.metadata = metadata
        memory.updated_at = datetime.utcnow()
        
        if not memory.is_sensitive:
            try:
                embeddings = await self.llm.embed([value])
                memory.embedding = embeddings[0] if embeddings else None
            except Exception:
                pass
        
        await db.flush()
        return memory
    
    async def delete_memory(
        self,
        db: AsyncSession,
        user_id: str,
        category: str,
        key: str,
    ) -> bool:
        memory = await self.get_memory(db, user_id, category, key)
        if not memory:
            return False
        await db.delete(memory)
        return True
    
    async def list_memories(
        self,
        db: AsyncSession,
        user_id: str,
        category: Optional[str] = None,
        limit: int = 100,
    ) -> List[Memory]:
        query = select(Memory).where(Memory.user_id == user_id)
        if category:
            query = query.where(Memory.category == category)
        query = query.order_by(Memory.updated_at.desc()).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def search_memories(
        self,
        db: AsyncSession,
        user_id: str,
        query: str,
        category: Optional[str] = None,
        limit: int = 10,
    ) -> List[Memory]:
        if not query:
            return await self.list_memories(db, user_id, category, limit)
        
        try:
            query_embedding = (await self.llm.embed([query]))[0]
        except Exception:
            return await self.list_memories(db, user_id, category, limit)
        
        base_query = select(Memory).where(Memory.user_id == user_id)
        if category:
            base_query = base_query.where(Memory.category == category)
        
        result = await db.execute(base_query)
        memories = list(result.scalars().all())
        
        if not memories:
            return []
        
        scored = []
        for memory in memories:
            if memory.embedding:
                similarity = self._cosine_similarity(query_embedding, memory.embedding)
                scored.append((similarity, memory))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored[:limit]]
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        if len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
    
    async def get_conversation_context(
        self,
        db: AsyncSession,
        conversation_id: str,
        limit: int = 20,
    ) -> List[Message]:
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        messages = list(result.scalars().all())
        messages.reverse()
        return messages
    
    async def save_conversation_message(
        self,
        db: AsyncSession,
        conversation_id: str,
        role: str,
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        tool_call_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Message:
        message = Message(
            id=str(uuid4()),
            conversation_id=conversation_id,
            role=role,
            content=content,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
            metadata=metadata or {},
        )
        db.add(message)
        await db.flush()
        return message
    
    async def create_conversation(
        self,
        db: AsyncSession,
        user_id: str,
        title: str,
        system_prompt: Optional[str] = None,
        model_provider: str = "ollama",
        model_name: str = "llama3.2:3b",
    ) -> Conversation:
        conversation = Conversation(
            id=str(uuid4()),
            user_id=user_id,
            title=title,
            system_prompt=system_prompt,
            model_provider=model_provider,
            model_name=model_name,
        )
        db.add(conversation)
        await db.flush()
        return conversation
    
    async def get_user_conversations(
        self,
        db: AsyncSession,
        user_id: str,
        include_archived: bool = False,
        limit: int = 50,
    ) -> List[Conversation]:
        query = select(Conversation).where(Conversation.user_id == user_id)
        if not include_archived:
            query = query.where(Conversation.is_archived == False)
        query = query.order_by(Conversation.updated_at.desc()).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())