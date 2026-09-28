from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.database.session import init_db, close_db
from app.tools.registry import tool_registry
from app.tools import register_core_tools
from app.integrations.github.client import GitHubClient
from app.plugins.browser.manager import browser_manager
from app.scheduler.manager import SchedulerManager
from app.services.notifications import NotificationService
from app.events.bus import event_bus
from app.models.providers import create_llm_provider
from app.agent.orchestrator import AgentOrchestrator
from app.memory.manager import MemoryManager


llm_provider = None
github_client = None
scheduler = None
notification_service = None
agent_orchestrator = None
memory_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global llm_provider, github_client, scheduler, notification_service, agent_orchestrator, memory_manager
    
    await init_db()
    
    register_core_tools()
    
    llm_provider = create_llm_provider(
        settings.MODEL_PROVIDER,
        settings.MODEL_NAME,
        base_url=settings.OLLAMA_BASE_URL,
        api_key=settings.OPENAI_API_KEY,
    )
    
    github_client = GitHubClient(settings.GITHUB_TOKEN)
    register_github_tools(github_client)
    
    if settings.ENABLE_BROWSER:
        await browser_manager.start()
        register_browser_tools(browser_manager)
    
    scheduler = SchedulerManager()
    if settings.ENABLE_SCHEDULER:
        scheduler.start()
        register_scheduler_tools(scheduler)
    
    notification_service = NotificationService()
    if settings.ENABLE_NOTIFICATIONS:
        register_notification_tools(notification_service)
    
    agent_orchestrator = AgentOrchestrator(llm_provider)
    memory_manager = MemoryManager(llm_provider)
    
    yield
    
    if settings.ENABLE_BROWSER:
        await browser_manager.stop()
    if settings.ENABLE_SCHEDULER:
        scheduler.shutdown()
    await close_db()


app = FastAPI(
    title=settings.AGENT_NAME,
    version=settings.AGENT_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import auth, chat, tasks, tools, pc, files, github, automations, memory, settings as settings_api, notifications, ws

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(tools.router, prefix="/api/tools", tags=["tools"])
app.include_router(pc.router, prefix="/api/pc", tags=["pc"])
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(github.router, prefix="/api/github", tags=["github"])
app.include_router(automations.router, prefix="/api/automations", tags=["automations"])
app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
app.include_router(settings_api.router, prefix="/api/settings", tags=["settings"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(ws.router, prefix="/ws", tags=["websocket"])


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": settings.AGENT_VERSION}


@app.get("/api/tools")
async def list_tools():
    return {"tools": tool_registry.list_tools()}


frontend_path = settings.DATA_DIR.parent / "frontend" / "dist"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")


def register_github_tools(client: GitHubClient):
    from app.tools.github_tools import (
        InspectRepositoryTool, ListIssuesTool, InspectIssueTool, CreateIssueTool,
        CommentIssueTool, ListPullRequestsTool, InspectPullRequestTool,
        CreateBranchTool, CreateCommitTool, CreatePullRequestTool,
        TriggerWorkflowTool, InspectWorkflowTool, DownloadArtifactTool,
    )
    
    tools = [
        InspectRepositoryTool(client),
        ListIssuesTool(client),
        InspectIssueTool(client),
        CreateIssueTool(client),
        CommentIssueTool(client),
        ListPullRequestsTool(client),
        InspectPullRequestTool(client),
        CreateBranchTool(client),
        CreateCommitTool(client),
        CreatePullRequestTool(client),
        TriggerWorkflowTool(client),
        InspectWorkflowTool(client),
        DownloadArtifactTool(client),
    ]
    
    for tool in tools:
        tool_registry.register(tool)


def register_browser_tools(manager):
    from app.tools.browser_tools import (
        OpenPageTool, NavigateTool, ExtractPageTextTool, TakeScreenshotTool,
        ClickElementTool, FillFormTool, ClosePageTool,
    )
    
    tools = [
        OpenPageTool(manager),
        NavigateTool(manager),
        ExtractPageTextTool(manager),
        TakeScreenshotTool(manager),
        ClickElementTool(manager),
        FillFormTool(manager),
        ClosePageTool(manager),
    ]
    
    for tool in tools:
        tool_registry.register(tool)


def register_scheduler_tools(manager: SchedulerManager):
    from app.tools.scheduler_tools import (
        CreateTaskTool, UpdateTaskTool, DeleteTaskTool, ListTasksTool, RunTaskNowTool,
    )
    
    tools = [
        CreateTaskTool(manager),
        UpdateTaskTool(manager),
        DeleteTaskTool(manager),
        ListTasksTool(manager),
        RunTaskNowTool(manager),
    ]
    
    for tool in tools:
        tool_registry.register(tool)


def register_notification_tools(service: NotificationService):
    from app.tools.notification_tools import (
        SendMobileNotificationTool, SendEmailTool, SendWebNotificationTool,
    )
    
    tools = [
        SendMobileNotificationTool(service),
        SendEmailTool(service),
        SendWebNotificationTool(service),
    ]
    
    for tool in tools:
        tool_registry.register(tool)