import asyncio
import subprocess
import shlex
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field

from app.tools.registry import BaseTool, ToolInputSchema, ToolOutput, PermissionLevel
from app.security.permissions import Permission
from app.config import settings


class RunCommandInput(ToolInputSchema):
    command: str
    cwd: Optional[str] = Field(default=None)
    timeout: int = Field(default=60, ge=1, le=300)
    shell: bool = Field(default=False)
    env: Optional[dict] = Field(default=None)


class RunCommandTool(BaseTool):
    name = "run_command"
    description = "Run a shell command"
    permission_level = PermissionLevel.DEVELOPER
    required_permissions = [Permission.TERMINAL_EXECUTE]
    input_schema = RunCommandInput
    
    ALLOWED_COMMANDS = {
        "ls", "dir", "cd", "pwd", "cat", "type", "echo", "grep", "find",
        "git", "npm", "node", "python", "pip", "poetry", "cargo", "go",
        "flutter", "dart", "dotnet", "msbuild", "powershell", "cmd",
        "mkdir", "rmdir", "cp", "copy", "mv", "move", "rm", "del",
        "chmod", "chown", "chgrp", "touch", "head", "tail", "less",
        "more", "wc", "sort", "uniq", "awk", "sed", "curl", "wget",
        "ssh", "scp", "rsync", "tar", "zip", "unzip", "gzip", "gunzip",
        "docker", "docker-compose", "kubectl", "helm", "terraform",
        "ansible", "vagrant", "make", "cmake", "ninja", "meson",
    }
    
    def _validate_command(self, command: str) -> bool:
        parts = shlex.split(command)
        if not parts:
            return False
        base_cmd = Path(parts[0]).name.lower()
        return base_cmd in self.ALLOWED_COMMANDS
    
    def _resolve_cwd(self, cwd: Optional[str]) -> Path:
        if cwd:
            base = Path(settings.DATA_DIR).resolve()
            target = (base / cwd).resolve()
            if not target.is_relative_to(base):
                raise ValueError("Path traversal attempt detected")
            return target
        return Path(settings.DATA_DIR).resolve()
    
    async def execute(self, input_data: RunCommandInput) -> ToolOutput:
        try:
            if not self._validate_command(input_data.command):
                return ToolOutput(success=False, error="Command not in allowlist")
            
            cwd = self._resolve_cwd(input_data.cwd)
            
            env = dict(os.environ)
            if input_data.env:
                env.update(input_data.env)
            
            if input_data.shell:
                process = await asyncio.create_subprocess_shell(
                    input_data.command,
                    cwd=cwd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env,
                )
            else:
                args = shlex.split(input_data.command)
                process = await asyncio.create_subprocess_exec(
                    *args,
                    cwd=cwd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env,
                )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=input_data.timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolOutput(success=False, error=f"Command timed out after {input_data.timeout}s")
            
            output = stdout.decode("utf-8", errors="replace")
            error_output = stderr.decode("utf-8", errors="replace")
            
            if len(output) > settings.MAX_COMMAND_OUTPUT_CHARS:
                output = output[:settings.MAX_COMMAND_OUTPUT_CHARS] + "\n... (truncated)"
            if len(error_output) > settings.MAX_COMMAND_OUTPUT_CHARS:
                error_output = error_output[:settings.MAX_COMMAND_OUTPUT_CHARS] + "\n... (truncated)"
            
            return ToolOutput(success=process.returncode == 0, data={
                "stdout": output,
                "stderr": error_output,
                "return_code": process.returncode,
                "command": input_data.command,
                "cwd": str(cwd.relative_to(settings.DATA_DIR)) if cwd != settings.DATA_DIR else ".",
            })
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class RunPowerShellInput(ToolInputSchema):
    command: str
    cwd: Optional[str] = Field(default=None)
    timeout: int = Field(default=60, ge=1, le=300)


class RunPowerShellTool(BaseTool):
    name = "run_powershell"
    description = "Run a PowerShell command"
    permission_level = PermissionLevel.DEVELOPER
    required_permissions = [Permission.TERMINAL_EXECUTE]
    input_schema = RunPowerShellInput
    
    def _resolve_cwd(self, cwd: Optional[str]) -> Path:
        if cwd:
            base = Path(settings.DATA_DIR).resolve()
            target = (base / cwd).resolve()
            if not target.is_relative_to(base):
                raise ValueError("Path traversal attempt detected")
            return target
        return Path(settings.DATA_DIR).resolve()
    
    async def execute(self, input_data: RunPowerShellInput) -> ToolOutput:
        try:
            cwd = self._resolve_cwd(input_data.cwd)
            
            process = await asyncio.create_subprocess_exec(
                "powershell.exe", "-Command", input_data.command,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=input_data.timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolOutput(success=False, error=f"Command timed out after {input_data.timeout}s")
            
            output = stdout.decode("utf-8", errors="replace")
            error_output = stderr.decode("utf-8", errors="replace")
            
            return ToolOutput(success=process.returncode == 0, data={
                "stdout": output[:settings.MAX_COMMAND_OUTPUT_CHARS],
                "stderr": error_output[:settings.MAX_COMMAND_OUTPUT_CHARS],
                "return_code": process.returncode,
                "command": input_data.command,
            })
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class RunPythonInput(ToolInputSchema):
    script: str
    cwd: Optional[str] = Field(default=None)
    timeout: int = Field(default=120, ge=1, le=600)
    args: List[str] = Field(default_factory=list)


class RunPythonTool(BaseTool):
    name = "run_python"
    description = "Run a Python script"
    permission_level = PermissionLevel.DEVELOPER
    required_permissions = [Permission.TERMINAL_EXECUTE]
    input_schema = RunPythonInput
    
    def _resolve_cwd(self, cwd: Optional[str]) -> Path:
        if cwd:
            base = Path(settings.DATA_DIR).resolve()
            target = (base / cwd).resolve()
            if not target.is_relative_to(base):
                raise ValueError("Path traversal attempt detected")
            return target
        return Path(settings.DATA_DIR).resolve()
    
    async def execute(self, input_data: RunPythonInput) -> ToolOutput:
        try:
            cwd = self._resolve_cwd(input_data.cwd)
            
            cmd = ["python", "-c", input_data.script] + input_data.args
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=input_data.timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolOutput(success=False, error=f"Script timed out after {input_data.timeout}s")
            
            output = stdout.decode("utf-8", errors="replace")
            error_output = stderr.decode("utf-8", errors="replace")
            
            return ToolOutput(success=process.returncode == 0, data={
                "stdout": output[:settings.MAX_COMMAND_OUTPUT_CHARS],
                "stderr": error_output[:settings.MAX_COMMAND_OUTPUT_CHARS],
                "return_code": process.returncode,
            })
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class RunGitInput(ToolInputSchema):
    args: List[str]
    cwd: Optional[str] = Field(default=None)
    timeout: int = Field(default=60, ge=1, le=300)


class RunGitTool(BaseTool):
    name = "run_git"
    description = "Run a git command"
    permission_level = PermissionLevel.DEVELOPER
    required_permissions = [Permission.TERMINAL_EXECUTE, Permission.GIT_WRITE]
    input_schema = RunGitInput
    
    def _resolve_cwd(self, cwd: Optional[str]) -> Path:
        if cwd:
            base = Path(settings.DATA_DIR).resolve()
            target = (base / cwd).resolve()
            if not target.is_relative_to(base):
                raise ValueError("Path traversal attempt detected")
            return target
        return Path(settings.DATA_DIR).resolve()
    
    async def execute(self, input_data: RunGitInput) -> ToolOutput:
        try:
            cwd = self._resolve_cwd(input_data.cwd)
            
            cmd = ["git"] + input_data.args
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=input_data.timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolOutput(success=False, error=f"Command timed out after {input_data.timeout}s")
            
            output = stdout.decode("utf-8", errors="replace")
            error_output = stderr.decode("utf-8", errors="replace")
            
            return ToolOutput(success=process.returncode == 0, data={
                "stdout": output[:settings.MAX_COMMAND_OUTPUT_CHARS],
                "stderr": error_output[:settings.MAX_COMMAND_OUTPUT_CHARS],
                "return_code": process.returncode,
                "command": " ".join(cmd),
            })
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class RunNpmInput(ToolInputSchema):
    command: str
    cwd: Optional[str] = Field(default=None)
    timeout: int = Field(default=180, ge=1, le=600)


class RunNpmTool(BaseTool):
    name = "run_npm"
    description = "Run an npm command"
    permission_level = PermissionLevel.DEVELOPER
    required_permissions = [Permission.TERMINAL_EXECUTE, Permission.DEV_BUILD]
    input_schema = RunNpmInput
    
    def _resolve_cwd(self, cwd: Optional[str]) -> Path:
        if cwd:
            base = Path(settings.DATA_DIR).resolve()
            target = (base / cwd).resolve()
            if not target.is_relative_to(base):
                raise ValueError("Path traversal attempt detected")
            return target
        return Path(settings.DATA_DIR).resolve()
    
    async def execute(self, input_data: RunNpmInput) -> ToolOutput:
        try:
            cwd = self._resolve_cwd(input_data.cwd)
            
            cmd = ["npm"] + shlex.split(input_data.command)
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=input_data.timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolOutput(success=False, error=f"Command timed out after {input_data.timeout}s")
            
            output = stdout.decode("utf-8", errors="replace")
            error_output = stderr.decode("utf-8", errors="replace")
            
            return ToolOutput(success=process.returncode == 0, data={
                "stdout": output[:settings.MAX_COMMAND_OUTPUT_CHARS],
                "stderr": error_output[:settings.MAX_COMMAND_OUTPUT_CHARS],
                "return_code": process.returncode,
            })
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class RunFlutterInput(ToolInputSchema):
    command: str
    cwd: Optional[str] = Field(default=None)
    timeout: int = Field(default=300, ge=1, le=900)


class RunFlutterTool(BaseTool):
    name = "run_flutter"
    description = "Run a flutter command"
    permission_level = PermissionLevel.DEVELOPER
    required_permissions = [Permission.TERMINAL_EXECUTE, Permission.DEV_BUILD]
    input_schema = RunFlutterInput
    
    def _resolve_cwd(self, cwd: Optional[str]) -> Path:
        if cwd:
            base = Path(settings.DATA_DIR).resolve()
            target = (base / cwd).resolve()
            if not target.is_relative_to(base):
                raise ValueError("Path traversal attempt detected")
            return target
        return Path(settings.DATA_DIR).resolve()
    
    async def execute(self, input_data: RunFlutterInput) -> ToolOutput:
        try:
            cwd = self._resolve_cwd(input_data.cwd)
            
            cmd = ["flutter"] + shlex.split(input_data.command)
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=input_data.timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolOutput(success=False, error=f"Command timed out after {input_data.timeout}s")
            
            output = stdout.decode("utf-8", errors="replace")
            error_output = stderr.decode("utf-8", errors="replace")
            
            return ToolOutput(success=process.returncode == 0, data={
                "stdout": output[:settings.MAX_COMMAND_OUTPUT_CHARS],
                "stderr": error_output[:settings.MAX_COMMAND_OUTPUT_CHARS],
                "return_code": process.returncode,
            })
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class RunDockerInput(ToolInputSchema):
    command: str
    timeout: int = Field(default=300, ge=1, le=900)


class RunDockerTool(BaseTool):
    name = "run_docker"
    description = "Run a docker command"
    permission_level = PermissionLevel.SYSTEM
    required_permissions = [Permission.TERMINAL_EXECUTE, Permission.TERMINAL_ADMIN]
    input_schema = RunDockerInput
    
    async def execute(self, input_data: RunDockerInput) -> ToolOutput:
        try:
            cmd = ["docker"] + shlex.split(input_data.command)
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=input_data.timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolOutput(success=False, error=f"Command timed out after {input_data.timeout}s")
            
            output = stdout.decode("utf-8", errors="replace")
            error_output = stderr.decode("utf-8", errors="replace")
            
            return ToolOutput(success=process.returncode == 0, data={
                "stdout": output[:settings.MAX_COMMAND_OUTPUT_CHARS],
                "stderr": error_output[:settings.MAX_COMMAND_OUTPUT_CHARS],
                "return_code": process.returncode,
            })
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


import os