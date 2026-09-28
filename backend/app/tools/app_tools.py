import asyncio
import subprocess
import shlex
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field

from app.tools.registry import BaseTool, ToolInputSchema, ToolOutput, PermissionLevel
from app.security.permissions import Permission
from app.config import settings


class OpenApplicationInput(ToolInputSchema):
    name: str
    args: List[str] = Field(default_factory=[])


class OpenApplicationTool(BaseTool):
    name = "open_application"
    description = "Launch an application"
    permission_level = PermissionLevel.SAFE_LOCAL
    required_permissions = [Permission.APP_LAUNCH]
    input_schema = OpenApplicationInput
    
    ALLOWED_APPS = {
        "code", "vscode", "notepad", "notepad++", "sublime", "vim", "nvim",
        "chrome", "firefox", "edge", "brave",
        "explorer", "cmd", "powershell", "wt", "terminal",
        "git", "git-gui", "gitk",
        "docker", "docker-desktop",
        "postman", "insomnia",
        "spotify", "vlc", "discord", "slack", "teams",
        "obsidian", "notion", "onenote",
    }
    
    def _find_executable(self, name: str) -> Optional[str]:
        name_lower = name.lower()
        if name_lower in self.ALLOWED_APPS:
            return name
        
        # Try to find in PATH
        import shutil
        found = shutil.which(name)
        if found:
            return found
        
        # Common Windows locations
        common_paths = [
            r"C:\Program Files",
            r"C:\Program Files (x86)",
            os.path.expanduser(r"~\AppData\Local\Programs"),
            os.path.expanduser(r"~\AppData\Local"),
        ]
        
        for base in common_paths:
            for root, dirs, files in os.walk(base):
                for f in files:
                    if f.lower().startswith(name_lower) and f.endswith(".exe"):
                        return os.path.join(root, f)
        
        return None
    
    async def execute(self, input_data: OpenApplicationInput) -> ToolOutput:
        try:
            executable = self._find_executable(input_data.name)
            if not executable:
                return ToolOutput(success=False, error=f"Application not found or not allowed: {input_data.name}")
            
            cmd = [executable] + input_data.args
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
                start_new_session=True,
            )
            
            return ToolOutput(success=True, data={
                "application": input_data.name,
                "pid": process.pid,
                "command": " ".join(cmd),
            })
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class CloseApplicationInput(ToolInputSchema):
    name: str
    force: bool = Field(default=False)


class CloseApplicationTool(BaseTool):
    name = "close_application"
    description = "Close an application by name"
    permission_level = PermissionLevel.SAFE_LOCAL
    required_permissions = [Permission.APP_CLOSE]
    input_schema = CloseApplicationInput
    
    async def execute(self, input_data: CloseApplicationInput) -> ToolOutput:
        try:
            import psutil
            
            closed = []
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    if input_data.name.lower() in proc.info['name'].lower():
                        if input_data.force:
                            proc.kill()
                        else:
                            proc.terminate()
                        closed.append(proc.info['pid'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if not closed:
                return ToolOutput(success=False, error=f"No process found for: {input_data.name}")
            
            return ToolOutput(success=True, data={
                "application": input_data.name,
                "closed_pids": closed,
            })
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class LaunchURLInput(ToolInputSchema):
    url: str
    browser: Optional[str] = Field(default=None)


class LaunchURLTool(BaseTool):
    name = "launch_url"
    description = "Open a URL in the default browser or specified browser"
    permission_level = PermissionLevel.SAFE_LOCAL
    required_permissions = [Permission.APP_LAUNCH]
    input_schema = LaunchURLInput
    
    async def execute(self, input_data: LaunchURLInput) -> ToolOutput:
        try:
            import webbrowser
            
            if input_data.browser:
                browser = webbrowser.get(input_data.browser)
            else:
                browser = webbrowser.get()
            
            result = browser.open(input_data.url)
            
            return ToolOutput(success=result, data={
                "url": input_data.url,
                "opened": result,
            })
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


import os