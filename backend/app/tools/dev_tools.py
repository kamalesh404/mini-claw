import json
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.tools.registry import BaseTool, ToolInputSchema, ToolOutput, PermissionLevel
from app.security.permissions import Permission
from app.config import settings


class InspectProjectInput(ToolInputSchema):
    path: str = Field(default=".")


class InspectProjectTool(BaseTool):
    name = "inspect_project"
    description = "Analyze project structure and detect project type"
    permission_level = PermissionLevel.READ_ONLY
    required_permissions = [Permission.DEV_READ]
    input_schema = InspectProjectInput
    
    def _resolve_path(self, path: str) -> Path:
        base = Path(settings.DATA_DIR).resolve()
        target = (base / path).resolve()
        if not target.is_relative_to(base):
            raise ValueError("Path traversal attempt detected")
        return target
    
    def _detect_project_type(self, path: Path) -> Dict[str, Any]:
        result = {"type": "unknown", "configs": [], "languages": []}
        
        # Check for common config files
        configs = {
            "package.json": "node",
            "pyproject.toml": "python",
            "setup.py": "python",
            "requirements.txt": "python",
            "Cargo.toml": "rust",
            "go.mod": "go",
            "pom.xml": "java-maven",
            "build.gradle": "java-gradle",
            "pubspec.yaml": "flutter",
            "composer.json": "php",
            "Gemfile": "ruby",
            "CMakeLists.txt": "cpp-cmake",
            "Makefile": "make",
            "meson.build": "meson",
        }
        
        for config, lang in configs.items():
            if (path / config).exists():
                result["configs"].append(config)
                if lang not in result["languages"]:
                    result["languages"].append(lang)
        
        if result["languages"]:
            result["type"] = result["languages"][0]
        
        # Check for git
        if (path / ".git").exists():
            result["git"] = True
        
        return result
    
    async def execute(self, input_data: InspectProjectInput) -> ToolOutput:
        try:
            target_path = self._resolve_path(input_data.path)
            
            if not target_path.exists():
                return ToolOutput(success=False, error=f"Path does not exist: {input_data.path}")
            
            project_info = self._detect_project_type(target_path)
            
            # Get directory structure
            structure = {}
            for item in target_path.iterdir():
                if item.name.startswith(".") and item.name != ".git":
                    continue
                if item.is_dir():
                    structure[item.name] = "dir"
                else:
                    structure[item.name] = "file"
            
            project_info["structure"] = structure
            project_info["path"] = input_data.path
            
            return ToolOutput(success=True, data=project_info)
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class InstallDependenciesInput(ToolInputSchema):
    path: str = Field(default=".")
    package_manager: Optional[str] = Field(default=None)


class InstallDependenciesTool(BaseTool):
    name = "install_dependencies"
    description = "Install project dependencies"
    permission_level = PermissionLevel.DEVELOPER
    required_permissions = [Permission.DEV_WRITE, Permission.DEV_BUILD]
    input_schema = InstallDependenciesInput
    
    def _resolve_path(self, path: str) -> Path:
        base = Path(settings.DATA_DIR).resolve()
        target = (base / path).resolve()
        if not target.is_relative_to(base):
            raise ValueError("Path traversal attempt detected")
        return target
    
    def _get_install_command(self, path: Path, package_manager: Optional[str]) -> Optional[List[str]]:
        if package_manager:
            return shlex.split(package_manager)
        
        if (path / "package.json").exists():
            if (path / "pnpm-lock.yaml").exists():
                return ["pnpm", "install"]
            elif (path / "yarn.lock").exists():
                return ["yarn", "install"]
            else:
                return ["npm", "install"]
        elif (path / "pyproject.toml").exists() or (path / "requirements.txt").exists():
            if (path / "poetry.lock").exists():
                return ["poetry", "install"]
            elif (path / "Pipfile.lock").exists():
                return ["pipenv", "install"]
            else:
                return ["pip", "install", "-r", "requirements.txt"]
        elif (path / "Cargo.toml").exists():
            return ["cargo", "build"]
        elif (path / "go.mod").exists():
            return ["go", "mod", "download"]
        elif (path / "pubspec.yaml").exists():
            return ["flutter", "pub", "get"]
        elif (path / "composer.json").exists():
            return ["composer", "install"]
        
        return None
    
    import shlex
    
    async def execute(self, input_data: InstallDependenciesInput) -> ToolOutput:
        try:
            target_path = self._resolve_path(input_data.path)
            
            if not target_path.exists():
                return ToolOutput(success=False, error=f"Path does not exist: {input_data.path}")
            
            cmd = self._get_install_command(target_path, input_data.package_manager)
            if not cmd:
                return ToolOutput(success=False, error="Could not determine package manager")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=target_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await process.communicate()
            
            output = stdout.decode("utf-8", errors="replace")
            error_output = stderr.decode("utf-8", errors="replace")
            
            return ToolOutput(success=process.returncode == 0, data={
                "command": " ".join(cmd),
                "stdout": output[:settings.MAX_COMMAND_OUTPUT_CHARS],
                "stderr": error_output[:settings.MAX_COMMAND_OUTPUT_CHARS],
                "return_code": process.returncode,
            })
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class RunTestsInput(ToolInputSchema):
    path: str = Field(default=".")
    test_command: Optional[str] = Field(default=None)
    pattern: Optional[str] = Field(default=None)


class RunTestsTool(BaseTool):
    name = "run_tests"
    description = "Run project tests"
    permission_level = PermissionLevel.READ_ONLY
    required_permissions = [Permission.DEV_TEST]
    input_schema = RunTestsInput
    
    def _resolve_path(self, path: str) -> Path:
        base = Path(settings.DATA_DIR).resolve()
        target = (base / path).resolve()
        if not target.is_relative_to(base):
            raise ValueError("Path traversal attempt detected")
        return target
    
    def _get_test_command(self, path: Path, test_command: Optional[str], pattern: Optional[str]) -> Optional[List[str]]:
        if test_command:
            return shlex.split(test_command)
        
        if (path / "package.json").exists():
            if pattern:
                return ["npm", "test", "--", pattern]
            return ["npm", "test"]
        elif (path / "pyproject.toml").exists():
            if (path / "pytest.ini").exists() or (path / "pyproject.toml").exists():
                cmd = ["pytest"]
                if pattern:
                    cmd.extend(["-k", pattern])
                return cmd
            return ["python", "-m", "unittest"]
        elif (path / "Cargo.toml").exists():
            return ["cargo", "test"]
        elif (path / "go.mod").exists():
            cmd = ["go", "test", "./..."]
            if pattern:
                cmd.extend(["-run", pattern])
            return cmd
        elif (path / "pubspec.yaml").exists():
            return ["flutter", "test"]
        
        return None
    
    import shlex
    import asyncio
    
    async def execute(self, input_data: RunTestsInput) -> ToolOutput:
        try:
            target_path = self._resolve_path(input_data.path)
            
            if not target_path.exists():
                return ToolOutput(success=False, error=f"Path does not exist: {input_data.path}")
            
            cmd = self._get_test_command(target_path, input_data.test_command, input_data.pattern)
            if not cmd:
                return ToolOutput(success=False, error="Could not determine test command")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=target_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await process.communicate()
            
            output = stdout.decode("utf-8", errors="replace")
            error_output = stderr.decode("utf-8", errors="replace")
            
            return ToolOutput(success=process.returncode == 0, data={
                "command": " ".join(cmd),
                "stdout": output[:settings.MAX_COMMAND_OUTPUT_CHARS],
                "stderr": error_output[:settings.MAX_COMMAND_OUTPUT_CHARS],
                "return_code": process.returncode,
            })
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class RunLinterInput(ToolInputSchema):
    path: str = Field(default=".")
    linter_command: Optional[str] = Field(default=None)


class RunLinterTool(BaseTool):
    name = "run_linter"
    description = "Run code linter"
    permission_level = PermissionLevel.READ_ONLY
    required_permissions = [Permission.DEV_READ]
    input_schema = RunLinterInput
    
    def _resolve_path(self, path: str) -> Path:
        base = Path(settings.DATA_DIR).resolve()
        target = (base / path).resolve()
        if not target.is_relative_to(base):
            raise ValueError("Path traversal attempt detected")
        return target
    
    def _get_linter_command(self, path: Path, linter_command: Optional[str]) -> Optional[List[str]]:
        if linter_command:
            return shlex.split(linter_command)
        
        if (path / "package.json").exists():
            return ["npm", "run", "lint"]
        elif (path / "pyproject.toml").exists():
            if (path / "ruff.toml").exists() or (path / "pyproject.toml").exists():
                return ["ruff", "check", "."]
            return ["flake8", "."]
        elif (path / "Cargo.toml").exists():
            return ["cargo", "clippy"]
        elif (path / "go.mod").exists():
            return ["golangci-lint", "run"]
        
        return None
    
    import shlex
    import asyncio
    
    async def execute(self, input_data: RunLinterInput) -> ToolOutput:
        try:
            target_path = self._resolve_path(input_data.path)
            
            if not target_path.exists():
                return ToolOutput(success=False, error=f"Path does not exist: {input_data.path}")
            
            cmd = self._get_linter_command(target_path, input_data.linter_command)
            if not cmd:
                return ToolOutput(success=False, error="Could not determine linter command")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=target_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await process.communicate()
            
            output = stdout.decode("utf-8", errors="replace")
            error_output = stderr.decode("utf-8", errors="replace")
            
            return ToolOutput(success=process.returncode == 0, data={
                "command": " ".join(cmd),
                "stdout": output[:settings.MAX_COMMAND_OUTPUT_CHARS],
                "stderr": error_output[:settings.MAX_COMMAND_OUTPUT_CHARS],
                "return_code": process.returncode,
            })
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class BuildProjectInput(ToolInputSchema):
    path: str = Field(default=".")
    build_command: Optional[str] = Field(default=None)
    target: Optional[str] = Field(default=None)


class BuildProjectTool(BaseTool):
    name = "build_project"
    description = "Build a project"
    permission_level = PermissionLevel.DEVELOPER
    required_permissions = [Permission.DEV_BUILD]
    input_schema = BuildProjectInput
    
    def _resolve_path(self, path: str) -> Path:
        base = Path(settings.DATA_DIR).resolve()
        target = (base / path).resolve()
        if not target.is_relative_to(base):
            raise ValueError("Path traversal attempt detected")
        return target
    
    def _get_build_command(self, path: Path, build_command: Optional[str], target: Optional[str]) -> Optional[List[str]]:
        if build_command:
            return shlex.split(build_command)
        
        if (path / "package.json").exists():
            if target:
                return ["npm", "run", f"build:{target}"]
            return ["npm", "run", "build"]
        elif (path / "pyproject.toml").exists():
            return ["python", "-m", "build"]
        elif (path / "Cargo.toml").exists():
            cmd = ["cargo", "build", "--release"]
            if target:
                cmd.extend(["--target", target])
            return cmd
        elif (path / "go.mod").exists():
            cmd = ["go", "build"]
            if target:
                cmd.extend(["-o", target])
            return cmd
        elif (path / "pubspec.yaml").exists():
            cmd = ["flutter", "build"]
            if target:
                cmd.append(target)
            return cmd
        elif (path / "CMakeLists.txt").exists():
            return ["cmake", "--build", "build"]
        
        return None
    
    import shlex
    import asyncio
    
    async def execute(self, input_data: BuildProjectInput) -> ToolOutput:
        try:
            target_path = self._resolve_path(input_data.path)
            
            if not target_path.exists():
                return ToolOutput(success=False, error=f"Path does not exist: {input_data.path}")
            
            cmd = self._get_build_command(target_path, input_data.build_command, input_data.target)
            if not cmd:
                return ToolOutput(success=False, error="Could not determine build command")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=target_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await process.communicate()
            
            output = stdout.decode("utf-8", errors="replace")
            error_output = stderr.decode("utf-8", errors="replace")
            
            return ToolOutput(success=process.returncode == 0, data={
                "command": " ".join(cmd),
                "stdout": output[:settings.MAX_COMMAND_OUTPUT_CHARS],
                "stderr": error_output[:settings.MAX_COMMAND_OUTPUT_CHARS],
                "return_code": process.returncode,
            })
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class InspectGitStatusInput(ToolInputSchema):
    path: str = Field(default=".")


class InspectGitStatusTool(BaseTool):
    name = "inspect_git_status"
    description = "Get git repository status"
    permission_level = PermissionLevel.READ_ONLY
    required_permissions = [Permission.GIT_READ]
    input_schema = InspectGitStatusInput
    
    def _resolve_path(self, path: str) -> Path:
        base = Path(settings.DATA_DIR).resolve()
        target = (base / path).resolve()
        if not target.is_relative_to(base):
            raise ValueError("Path traversal attempt detected")
        return target
    
    import shlex
    import asyncio
    
    async def _run_git(self, cwd: Path, args: List[str]) -> tuple[int, str, str]:
        process = await asyncio.create_subprocess_exec(
            "git", *args,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        return process.returncode, stdout.decode("utf-8", errors="replace"), stderr.decode("utf-8", errors="replace")
    
    async def execute(self, input_data: InspectGitStatusInput) -> ToolOutput:
        try:
            target_path = self._resolve_path(input_data.path)
            
            if not target_path.exists():
                return ToolOutput(success=False, error=f"Path does not exist: {input_data.path}")
            
            if not (target_path / ".git").exists():
                return ToolOutput(success=False, error="Not a git repository")
            
            # Get status
            code, stdout, stderr = await self._run_git(target_path, ["status", "--porcelain"])
            if code != 0:
                return ToolOutput(success=False, error=stderr)
            
            # Get current branch
            code, branch, _ = await self._run_git(target_path, ["branch", "--show-current"])
            branch = branch.strip() if code == 0 else "unknown"
            
            # Get last commit
            code, last_commit, _ = await self._run_git(target_path, ["log", "-1", "--oneline"])
            last_commit = last_commit.strip() if code == 0 else "unknown"
            
            # Get remote info
            code, remotes, _ = await self._run_git(target_path, ["remote", "-v"])
            
            # Parse status
            staged = []
            unstaged = []
            untracked = []
            
            for line in stdout.strip().split("\n"):
                if not line:
                    continue
                status = line[:2]
                file = line[3:]
                if status[0] != " ":
                    staged.append({"file": file, "status": status[0]})
                if status[1] != " ":
                    unstaged.append({"file": file, "status": status[1]})
                if status == "??":
                    untracked.append(file)
            
            return ToolOutput(success=True, data={
                "path": input_data.path,
                "branch": branch,
                "last_commit": last_commit,
                "staged": staged,
                "unstaged": unstaged,
                "untracked": untracked,
                "remotes": remotes.strip().split("\n") if remotes.strip() else [],
            })
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class CreateGitBranchInput(ToolInputSchema):
    path: str = Field(default=".")
    branch_name: str
    base_branch: Optional[str] = Field(default=None)


class CreateGitBranchTool(BaseTool):
    name = "create_git_branch"
    description = "Create a new git branch"
    permission_level = PermissionLevel.DEVELOPER
    required_permissions = [Permission.GIT_WRITE]
    input_schema = CreateGitBranchInput
    
    def _resolve_path(self, path: str) -> Path:
        base = Path(settings.DATA_DIR).resolve()
        target = (base / path).resolve()
        if not target.is_relative_to(base):
            raise ValueError("Path traversal attempt detected")
        return target
    
    import asyncio
    
    async def execute(self, input_data: CreateGitBranchInput) -> ToolOutput:
        try:
            target_path = self._resolve_path(input_data.path)
            
            if not target_path.exists():
                return ToolOutput(success=False, error=f"Path does not exist: {input_data.path}")
            
            if not (target_path / ".git").exists():
                return ToolOutput(success=False, error="Not a git repository")
            
            cmd = ["checkout", "-b", input_data.branch_name]
            if input_data.base_branch:
                cmd.append(input_data.base_branch)
            
            process = await asyncio.create_subprocess_exec(
                "git", *cmd,
                cwd=target_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await process.communicate()
            
            return ToolOutput(success=process.returncode == 0, data={
                "branch": input_data.branch_name,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
            })
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class CommitChangesInput(ToolInputSchema):
    path: str = Field(default=".")
    message: str
    add_all: bool = Field(default=True)
    files: List[str] = Field(default_factory=list)


class CommitChangesTool(BaseTool):
    name = "commit_changes"
    description = "Commit changes to git"
    permission_level = PermissionLevel.DEVELOPER
    required_permissions = [Permission.GIT_WRITE]
    input_schema = CommitChangesInput
    
    def _resolve_path(self, path: str) -> Path:
        base = Path(settings.DATA_DIR).resolve()
        target = (base / path).resolve()
        if not target.is_relative_to(base):
            raise ValueError("Path traversal attempt detected")
        return target
    
    import asyncio
    
    async def execute(self, input_data: CommitChangesInput) -> ToolOutput:
        try:
            target_path = self._resolve_path(input_data.path)
            
            if not target_path.exists():
                return ToolOutput(success=False, error=f"Path does not exist: {input_data.path}")
            
            if not (target_path / ".git").exists():
                return ToolOutput(success=False, error="Not a git repository")
            
            # Add files
            if input_data.add_all:
                process = await asyncio.create_subprocess_exec(
                    "git", "add", "-A",
                    cwd=target_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
            else:
                process = await asyncio.create_subprocess_exec(
                    "git", "add", *input_data.files,
                    cwd=target_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
            await process.communicate()
            
            if process.returncode != 0:
                return ToolOutput(success=False, error="Failed to add files")
            
            # Commit
            process = await asyncio.create_subprocess_exec(
                "git", "commit", "-m", input_data.message,
                cwd=target_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await process.communicate()
            
            return ToolOutput(success=process.returncode == 0, data={
                "message": input_data.message,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
            })
        except Exception as e:
            return ToolOutput(success=False, error=str(e))