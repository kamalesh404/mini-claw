# MiniClaw - Personal AI Automation Agent

<p align="center">
  <img src="docs/logo.svg" alt="MiniClaw Logo" width="200"/>
</p>

<p align="center">
  <strong>A self-hosted AI agent that runs on your Windows PC and can be controlled from anywhere.</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#configuration">Configuration</a> •
  <a href="#docs">Documentation</a>
</p>

---

## Features

### 🤖 AI Agent
- **Multi-LLM Support**: Ollama (local), OpenAI-compatible, Anthropic
- **Tool Calling**: Structured tool execution with validation
- **Streaming Responses**: Real-time chat streaming
- **Context Memory**: Long-term memory with semantic search

### 🛠️ Tool System (30+ Tools)
| Category | Tools |
|----------|-------|
| **System** | CPU, GPU, RAM, Disk, Network, Battery, Processes |
| **Files** | List, Search, Read, Create, Edit, Move, Copy, Delete |
| **Terminal** | Commands, PowerShell, Python, Git, npm, Flutter, Docker |
| **Apps** | Launch, Close, Open URL |
| **Development** | Inspect Project, Install Deps, Run Tests, Lint, Build, Git |
| **GitHub** | Repos, Issues, PRs, Branches, Commits, Workflows, Artifacts |
| **Browser** | Navigate, Extract, Screenshot, Click, Fill Forms |
| **Scheduler** | Cron, Interval, Event-triggered automations |
| **Notifications** | Push, Email, Web notifications |

### 🔐 Security First
- **Permission Levels**: 5 levels (Read-only → Dangerous)
- **Approval System**: Human-in-the-loop for sensitive operations
- **Audit Logging**: Every tool execution logged
- **No Direct Shell**: LLM never executes commands directly
- **Path Traversal Protection**: All file ops sandboxed
- **Command Allowlist**: Only approved commands executable

### 📱 Mobile-First UI
- **PWA**: Installable on Android/iOS
- **Real-time**: WebSocket for live updates
- **Responsive**: Works on phone, tablet, desktop
- **Dark Mode**: Default with system detection

### 🔄 Automation Engine
- **Cron Schedules**: "Every morning at 8 AM..."
- **Event Triggers**: "When GitHub workflow fails..."
- **Conditional**: "If disk < 10%, notify me"
- **Recurring**: Daily, weekly, custom intervals

### 🔗 Integrations
- **GitHub**: Full API (repos, issues, PRs, actions, webhooks)
- **Browser**: Playwright-based automation
- **Windows**: Process, file, app management
- **Docker**: Container management
- **Notifications**: Push, Email, Telegram, Discord

---

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Mobile    │────▶│  Agent Gateway   │────▶│  Agent Engine   │
│   / Web     │     │  (Auth, Rate     │     │  (Orchestrator) │
│   Client    │     │   Limit, CORS)   │     └────────┬────────┘
└─────────────┘     └──────────────────┘              │
                                                      ▼
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  GitHub     │◀───▶│  Integration     │◀───▶│  Tool Registry  │
│  Webhooks   │     │  Layer           │     │  (30+ Tools)    │
└─────────────┘     └──────────────────┘     └────────┬────────┘
                                                      ▼
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Scheduler  │────▶│  Event Bus       │◀───▶│  Memory System  │
│  (Cron,     │     │  (Pub/Sub)       │     │  (Vector + SQL) │
│   Events)   │     └──────────────────┘     └─────────────────┘
└─────────────┘
```

### Core Principles
1. **Local-First**: Runs on your hardware, no cloud dependency
2. **Modular**: Swap LLM, tools, memory, UI independently
3. **Secure by Default**: Approval required for mutations
4. **Observable**: Structured logs, metrics, audit trail
5. **Extensible**: Plugin architecture for custom tools

---

## Quick Start

### Prerequisites
- Windows 10/11
- Python 3.11+
- Node.js 20+
- Git
- Ollama (for local models)

### One-Command Install
```powershell
# Run in PowerShell as Administrator
Set-ExecutionPolicy Bypass -Scope Process -Force
irm https://raw.githubusercontent.com/yourusername/mini-claw/main/scripts/install.ps1 | iex
```

### Manual Install
```bash
# Clone repository
git clone https://github.com/yourusername/mini-claw.git
cd mini-claw

# Backend
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd ..\frontend
npm install
npm run build

# Initialize database
cd ..\backend
python -c "import asyncio; from app.database.session import init_db; asyncio.run(init_db())"

# Start services
# Terminal 1: Backend
cd backend && .\venv\Scripts\activate && python -m app.main

# Terminal 2: Frontend
cd frontend && npm run preview
```

### Start Ollama
```bash
# Install Ollama
winget install Ollama.Ollama

# Pull default model
ollama pull llama3.2:3b

# Start Ollama server
ollama serve
```

### Access
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs

---

## Configuration

Copy `.env.example` to `.env` and customize:

```bash
# Required
MODEL_PROVIDER=ollama
MODEL_NAME=llama3.2:3b
JWT_SECRET_KEY=your-32-char-secret-key

# Optional Integrations
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
TELEGRAM_BOT_TOKEN=...
DISCORD_BOT_TOKEN=...

# Remote Access (choose one)
TAILSCALE_AUTH_KEY=...        # For Tailscale
CLOUDFLARE_TUNNEL_TOKEN=...   # For Cloudflare Tunnel
```

### Model Providers

| Provider | Config | Notes |
|----------|--------|-------|
| **Ollama** | `MODEL_PROVIDER=ollama`<br>`OLLAMA_BASE_URL=http://localhost:11434` | Local, private, free |
| **OpenAI** | `MODEL_PROVIDER=openai`<br>`OPENAI_API_KEY=sk-...` | Cloud, paid |
| **Anthropic** | `MODEL_PROVIDER=anthropic`<br>`ANTHROPIC_API_KEY=sk-...` | Cloud, paid |
| **OpenAI-Compatible** | `MODEL_PROVIDER=openai_compatible`<br>`OPENAI_BASE_URL=http://your-server/v1` | Local/self-hosted |

### Low-VRAM Optimization (RTX 2050 4GB)
```bash
# Use quantized models
ollama pull llama3.2:3b-q4_K_M   # 4-bit quantized
ollama pull phi3:3.8b-q4_K_M     # Smaller, fast
ollama pull gemma2:2b-q4_K_M     # Tiny, very fast
```

---

## Usage Examples

### Chat with Agent
```
You: "Check my PC status"
Agent: Returns CPU, GPU, RAM, Disk, Battery info
```

### Run Development Tasks
```
You: "Build my Flutter project"
Agent: Finds project, runs `flutter pub get`, `flutter build apk`
```

### GitHub Operations
```
You: "Check my repo facebook/react"
Agent: Shows stars, forks, open issues, recent workflows
You: "Create issue: Fix login bug"
Agent: Creates issue with your description
```

### Automation
```
You: "Every day at 8 AM, summarize my GitHub activity"
Agent: Creates cron automation with GitHub summary action
```

### File Operations
```
You: "Find all .py files with 'TODO' comments"
Agent: Searches and lists matching files
```

### Approval Flow
```
You: "Delete the temp folder"
Agent: "I need your approval to: Delete C:\temp [Approve] [Reject]"
```

---

## Development

### Project Structure
```
mini-claw/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # REST endpoints
│   │   ├── agent/          # Agent orchestration
│   │   ├── tools/          # Tool registry & implementations
│   │   ├── models/         # LLM providers
│   │   ├── memory/         # Memory system
│   │   ├── scheduler/      # Automation engine
│   │   ├── security/       # Auth, permissions
│   │   ├── integrations/   # GitHub, etc.
│   │   └── events/         # Event bus
│   ├── tests/
│   └── plugins/
├── frontend/               # React + Vite + Tailwind
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── pages/          # Page components
│   │   ├── stores/         # Zustand state
│   │   └── services/       # API, WebSocket
│   └── public/
├── docker/                 # Docker configs
├── scripts/                # Windows install/start scripts
├── .github/workflows/      # CI/CD
└── docs/
```

### Running Tests
```bash
# Backend
cd backend
pytest --cov=app

# Frontend
cd frontend
npm run lint
npx tsc --noEmit
```

### Adding a Tool
```python
# backend/app/tools/my_tool.py
from app.tools.registry import BaseTool, ToolInputSchema, ToolOutput

class MyToolInput(ToolInputSchema):
    param: str

class MyTool(BaseTool):
    name = "my_tool"
    description = "Does something useful"
    permission_level = PermissionLevel.SAFE_LOCAL
    input_schema = MyToolInput
    
    async def execute(self, input_data: MyToolInput) -> ToolOutput:
        return ToolOutput(success=True, data={"result": "done"})

# Register in backend/app/tools/__init__.py
def register_my_tools():
    tool_registry.register(MyTool())
```

---

## Security

### Threat Model
- **Prompt Injection**: External content never becomes instructions
- **Command Injection**: All commands validated against allowlist
- **Path Traversal**: All paths resolved against sandbox root
- **SSRF**: Outbound requests restricted to allowlists
- **Credential Leakage**: Secrets never in logs, prompts, or DB

### Best Practices
1. Use Tailscale/Cloudflare Tunnel for remote access
2. Rotate JWT secrets regularly
3. Review audit logs periodically
4. Keep Ollama/models updated
5. Run `doctor.ps1` weekly

---

## Roadmap

### Phase 1 (MVP) ✅
- [x] FastAPI backend + React PWA
- [x] Local LLM (Ollama) + multi-provider
- [x] 30+ tools (system, files, terminal, dev, GitHub)
- [x] Auth, permissions, approval system
- [x] WebSocket real-time
- [x] SQLite + basic memory

### Phase 2
- [ ] Scheduler & automations
- [ ] Advanced memory (vector search)
- [ ] Notifications (push, email, Telegram)
- [ ] GitHub webhooks
- [ ] Browser automation (Playwright)

### Phase 3
- [ ] Flutter mobile app
- [ ] Self-hosted GitHub runner integration
- [ ] Voice support (STT/TTS)
- [ ] Plugin marketplace

### Phase 4
- [ ] Multi-agent collaboration
- [ ] RAG/knowledge base
- [ ] Desktop GUI automation
- [ ] Home automation integration

---

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Run `ruff`, `mypy`, `pytest`, `npm run lint`
5. Submit PR

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Security**: security@miniclaw.local

---

<p align="center">
  Made with ❤️ for developers who want their own AI assistant
</p>