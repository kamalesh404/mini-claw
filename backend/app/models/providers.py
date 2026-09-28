from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Dict, Any, Optional
from pydantic import BaseModel, Field
from dataclasses import dataclass


class Message(BaseModel):
    role: str = Field(pattern="^(system|user|assistant|tool)$")
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]


class LLMResponse(BaseModel):
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    finish_reason: str = "stop"
    usage: Optional[Dict[str, int]] = None


class LLMStreamChunk(BaseModel):
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    finish_reason: Optional[str] = None


class LLMProvider(ABC):
    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        self.config = kwargs
    
    @abstractmethod
    async def complete(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        pass
    
    @abstractmethod
    async def stream(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[LLMStreamChunk, None]:
        pass
    
    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        pass


class OllamaProvider(LLMProvider):
    def __init__(self, model_name: str, base_url: str = "http://localhost:11434", **kwargs):
        super().__init__(model_name, base_url=base_url, **kwargs)
        self.base_url = base_url
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            import ollama
            self._client = ollama.AsyncClient(host=self.base_url)
        return self._client
    
    async def complete(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        ollama_messages = [{"role": m.role, "content": m.content or ""} for m in messages]
        
        if tools:
            ollama_tools = []
            for tool in tools:
                ollama_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    }
                })
            response = await self.client.chat(
                model=self.model_name,
                messages=ollama_messages,
                tools=ollama_tools,
                options={"temperature": temperature, "num_predict": max_tokens or -1},
            )
        else:
            response = await self.client.chat(
                model=self.model_name,
                messages=ollama_messages,
                options={"temperature": temperature, "num_predict": max_tokens or -1},
            )
        
        message = response["message"]
        tool_calls = None
        if message.get("tool_calls"):
            tool_calls = []
            for tc in message["tool_calls"]:
                tool_calls.append({
                    "id": tc["function"]["name"],
                    "type": "function",
                    "function": {
                        "name": tc["function"]["name"],
                        "arguments": tc["function"]["arguments"],
                    }
                })
        
        return LLMResponse(
            content=message.get("content"),
            tool_calls=tool_calls,
            finish_reason="tool_calls" if tool_calls else "stop",
            usage={"prompt_tokens": response.get("prompt_eval_count", 0), "completion_tokens": response.get("eval_count", 0)},
        )
    
    async def stream(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[LLMStreamChunk, None]:
        ollama_messages = [{"role": m.role, "content": m.content or ""} for m in messages]
        
        if tools:
            ollama_tools = []
            for tool in tools:
                ollama_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    }
                })
            stream = await self.client.chat(
                model=self.model_name,
                messages=ollama_messages,
                tools=ollama_tools,
                options={"temperature": temperature, "num_predict": max_tokens or -1},
                stream=True,
            )
        else:
            stream = await self.client.chat(
                model=self.model_name,
                messages=ollama_messages,
                options={"temperature": temperature, "num_predict": max_tokens or -1},
                stream=True,
            )
        
        async for chunk in stream:
            message = chunk["message"]
            content = message.get("content")
            tool_calls = None
            if message.get("tool_calls"):
                tool_calls = []
                for tc in message["tool_calls"]:
                    tool_calls.append({
                        "id": tc["function"]["name"],
                        "type": "function",
                        "function": {
                            "name": tc["function"]["name"],
                            "arguments": tc["function"]["arguments"],
                        }
                    })
            
            yield LLMStreamChunk(
                content=content,
                tool_calls=tool_calls,
                finish_reason="tool_calls" if tool_calls else None,
            )
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            response = await self.client.embeddings(model=self.model_name, prompt=text)
            embeddings.append(response["embedding"])
        return embeddings
    
    async def health_check(self) -> bool:
        try:
            await self.client.list()
            return True
        except Exception:
            return False


class OpenAICompatibleProvider(LLMProvider):
    def __init__(
        self,
        model_name: str,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        **kwargs
    ):
        super().__init__(model_name, api_key=api_key, base_url=base_url, **kwargs)
        self.api_key = api_key
        self.base_url = base_url
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._client
    
    async def complete(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        openai_messages = [{"role": m.role, "content": m.content or ""} for m in messages]
        
        openai_tools = None
        if tools:
            openai_tools = []
            for tool in tools:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    }
                })
        
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=openai_messages,
            tools=openai_tools,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        message = response.choices[0].message
        tool_calls = None
        if message.tool_calls:
            tool_calls = []
            for tc in message.tool_calls:
                tool_calls.append({
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                })
        
        return LLMResponse(
            content=message.content,
            tool_calls=tool_calls,
            finish_reason=response.choices[0].finish_reason,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            } if response.usage else None,
        )
    
    async def stream(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[LLMStreamChunk, None]:
        openai_messages = [{"role": m.role, "content": m.content or ""} for m in messages]
        
        openai_tools = None
        if tools:
            openai_tools = []
            for tool in tools:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    }
                })
        
        stream = await self.client.chat.completions.create(
            model=self.model_name,
            messages=openai_messages,
            tools=openai_tools,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        
        async for chunk in stream:
            delta = chunk.choices[0].delta
            content = delta.content
            tool_calls = None
            if delta.tool_calls:
                tool_calls = []
                for tc in delta.tool_calls:
                    tool_calls.append({
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    })
            
            yield LLMStreamChunk(
                content=content,
                tool_calls=tool_calls,
                finish_reason=chunk.choices[0].finish_reason,
            )
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        response = await self.client.embeddings.create(
            model=self.config.get("embedding_model", "text-embedding-3-small"),
            input=texts,
        )
        return [d.embedding for d in response.data]
    
    async def health_check(self) -> bool:
        try:
            await self.client.models.list()
            return True
        except Exception:
            return False


class AnthropicProvider(LLMProvider):
    def __init__(self, model_name: str, api_key: str, **kwargs):
        super().__init__(model_name, api_key=api_key, **kwargs)
        self.api_key = api_key
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            from anthropic import AsyncAnthropic
            self._client = AsyncAnthropic(api_key=self.api_key)
        return self._client
    
    def _convert_messages(self, messages: List[Message]) -> tuple[str, List[Dict]]:
        system = ""
        converted = []
        for m in messages:
            if m.role == "system":
                system = m.content or ""
            elif m.role == "tool":
                converted.append({
                    "role": "user",
                    "content": f"Tool result ({m.name}): {m.content}",
                })
            else:
                converted.append({"role": m.role, "content": m.content or ""})
        return system, converted
    
    async def complete(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        system, converted = self._convert_messages(messages)
        
        anthropic_tools = None
        if tools:
            anthropic_tools = []
            for tool in tools:
                anthropic_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.parameters,
                })
        
        response = await self.client.messages.create(
            model=self.model_name,
            system=system,
            messages=converted,
            tools=anthropic_tools,
            temperature=temperature,
            max_tokens=max_tokens or 4096,
        )
        
        content = ""
        tool_calls = None
        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                if tool_calls is None:
                    tool_calls = []
                tool_calls.append({
                    "id": block.id,
                    "type": "function",
                    "function": {
                        "name": block.name,
                        "arguments": block.input,
                    }
                })
        
        return LLMResponse(
            content=content if content else None,
            tool_calls=tool_calls,
            finish_reason="tool_use" if tool_calls else response.stop_reason,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
            },
        )
    
    async def stream(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[LLMStreamChunk, None]:
        system, converted = self._convert_messages(messages)
        
        anthropic_tools = None
        if tools:
            anthropic_tools = []
            for tool in tools:
                anthropic_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.parameters,
                })
        
        stream = await self.client.messages.create(
            model=self.model_name,
            system=system,
            messages=converted,
            tools=anthropic_tools,
            temperature=temperature,
            max_tokens=max_tokens or 4096,
            stream=True,
        )
        
        async for chunk in stream:
            if chunk.type == "content_block_delta":
                if chunk.delta.type == "text_delta":
                    yield LLMStreamChunk(content=chunk.delta.text)
                elif chunk.delta.type == "input_json_delta":
                    yield LLMStreamChunk(content=chunk.delta.partial_json)
            elif chunk.type == "message_delta":
                if chunk.delta.stop_reason:
                    yield LLMStreamChunk(finish_reason=chunk.delta.stop_reason)
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        # Anthropic doesn't have embeddings, use a fallback
        raise NotImplementedError("Anthropic doesn't provide embeddings API")
    
    async def health_check(self) -> bool:
        try:
            await self.client.messages.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=10,
            )
            return True
        except Exception:
            return False


def create_llm_provider(provider_type: str, model_name: str, **kwargs) -> LLMProvider:
    providers = {
        "ollama": OllamaProvider,
        "openai": OpenAICompatibleProvider,
        "anthropic": AnthropicProvider,
        "openai_compatible": OpenAICompatibleProvider,
    }
    
    if provider_type not in providers:
        raise ValueError(f"Unknown provider: {provider_type}")
    
    return providers[provider_type](model_name, **kwargs)