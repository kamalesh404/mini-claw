import os
import shutil
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field

from app.tools.registry import BaseTool, ToolInputSchema, ToolOutput, PermissionLevel
from app.security.permissions import Permission
from app.config import settings


class ListFilesInput(ToolInputSchema):
    path: str = Field(default=".")
    recursive: bool = Field(default=False)
    include_hidden: bool = Field(default=False)
    pattern: Optional[str] = Field(default=None)


class ListFilesTool(BaseTool):
    name = "list_files"
    description = "List files and directories"
    permission_level = PermissionLevel.READ_ONLY
    required_permissions = [Permission.FILE_READ]
    input_schema = ListFilesInput
    
    def _resolve_path(self, path: str) -> Path:
        base = Path(settings.DATA_DIR).resolve()
        target = (base / path).resolve()
        if not target.is_relative_to(base):
            raise ValueError("Path traversal attempt detected")
        return target
    
    async def execute(self, input_data: ListFilesInput) -> ToolOutput:
        try:
            target_path = self._resolve_path(input_data.path)
            if not target_path.exists():
                return ToolOutput(success=False, error=f"Path does not exist: {input_data.path}")
            
            files = []
            if input_data.recursive:
                walker = target_path.rglob("*")
            else:
                walker = target_path.iterdir()
            
            for item in walker:
                if not input_data.include_hidden and item.name.startswith("."):
                    continue
                if input_data.pattern and not item.match(input_data.pattern):
                    continue
                
                stat = item.stat()
                files.append({
                    "name": item.name,
                    "path": str(item.relative_to(settings.DATA_DIR)),
                    "is_dir": item.is_dir(),
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                })
            
            return ToolOutput(success=True, data={"files": files, "path": input_data.path})
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class SearchFilesInput(ToolInputSchema):
    pattern: str
    path: str = Field(default=".")
    file_type: Optional[str] = Field(default=None, pattern="^(file|dir)$")
    max_results: int = Field(default=100, ge=1, le=1000)


class SearchFilesTool(BaseTool):
    name = "search_files"
    description = "Search for files matching a pattern"
    permission_level = PermissionLevel.READ_ONLY
    required_permissions = [Permission.FILE_READ]
    input_schema = SearchFilesInput
    
    def _resolve_path(self, path: str) -> Path:
        base = Path(settings.DATA_DIR).resolve()
        target = (base / path).resolve()
        if not target.is_relative_to(base):
            raise ValueError("Path traversal attempt detected")
        return target
    
    async def execute(self, input_data: SearchFilesInput) -> ToolOutput:
        try:
            target_path = self._resolve_path(input_data.path)
            if not target_path.exists():
                return ToolOutput(success=False, error=f"Path does not exist: {input_data.path}")
            
            results = []
            for item in target_path.rglob(input_data.pattern):
                if input_data.file_type == "file" and not item.is_file():
                    continue
                if input_data.file_type == "dir" and not item.is_dir():
                    continue
                
                stat = item.stat()
                results.append({
                    "name": item.name,
                    "path": str(item.relative_to(settings.DATA_DIR)),
                    "is_dir": item.is_dir(),
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                })
                
                if len(results) >= input_data.max_results:
                    break
            
            return ToolOutput(success=True, data={"results": results, "count": len(results)})
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class ReadFileInput(ToolInputSchema):
    path: str
    encoding: str = Field(default="utf-8")
    max_size: int = Field(default=1024*1024, ge=1, le=100*1024*1024)


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read file contents"
    permission_level = PermissionLevel.READ_ONLY
    required_permissions = [Permission.FILE_READ]
    input_schema = ReadFileInput
    
    def _resolve_path(self, path: str) -> Path:
        base = Path(settings.DATA_DIR).resolve()
        target = (base / path).resolve()
        if not target.is_relative_to(base):
            raise ValueError("Path traversal attempt detected")
        return target
    
    async def execute(self, input_data: ReadFileInput) -> ToolOutput:
        try:
            target_path = self._resolve_path(input_data.path)
            if not target_path.exists():
                return ToolOutput(success=False, error=f"File does not exist: {input_data.path}")
            if not target_path.is_file():
                return ToolOutput(success=False, error=f"Path is not a file: {input_data.path}")
            
            if target_path.stat().st_size > input_data.max_size:
                return ToolOutput(success=False, error=f"File too large (max {input_data.max_size} bytes)")
            
            content = target_path.read_text(encoding=input_data.encoding)
            return ToolOutput(success=True, data={
                "content": content,
                "path": input_data.path,
                "size": len(content),
            })
        except UnicodeDecodeError:
            return ToolOutput(success=False, error="File is not a text file")
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class CreateFileInput(ToolInputSchema):
    path: str
    content: str = Field(default="")
    encoding: str = Field(default="utf-8")
    overwrite: bool = Field(default=False)


class CreateFileTool(BaseTool):
    name = "create_file"
    description = "Create a new file"
    permission_level = PermissionLevel.SAFE_LOCAL
    required_permissions = [Permission.FILE_WRITE]
    input_schema = CreateFileInput
    
    def _resolve_path(self, path: str) -> Path:
        base = Path(settings.DATA_DIR).resolve()
        target = (base / path).resolve()
        if not target.is_relative_to(base):
            raise ValueError("Path traversal attempt detected")
        return target
    
    async def execute(self, input_data: CreateFileInput) -> ToolOutput:
        try:
            target_path = self._resolve_path(input_data.path)
            
            if target_path.exists() and not input_data.overwrite:
                return ToolOutput(success=False, error=f"File already exists: {input_data.path}")
            
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(input_data.content, encoding=input_data.encoding)
            
            return ToolOutput(success=True, data={
                "path": input_data.path,
                "size": len(input_data.content.encode(input_data.encoding)),
            })
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class EditFileInput(ToolInputSchema):
    path: str
    old_text: str
    new_text: str
    encoding: str = Field(default="utf-8")


class EditFileTool(BaseTool):
    name = "edit_file"
    description = "Edit a file by replacing text"
    permission_level = PermissionLevel.SAFE_LOCAL
    required_permissions = [Permission.FILE_WRITE]
    input_schema = EditFileInput
    
    def _resolve_path(self, path: str) -> Path:
        base = Path(settings.DATA_DIR).resolve()
        target = (base / path).resolve()
        if not target.is_relative_to(base):
            raise ValueError("Path traversal attempt detected")
        return target
    
    async def execute(self, input_data: EditFileInput) -> ToolOutput:
        try:
            target_path = self._resolve_path(input_data.path)
            if not target_path.exists():
                return ToolOutput(success=False, error=f"File does not exist: {input_data.path}")
            
            content = target_path.read_text(encoding=input_data.encoding)
            if input_data.old_text not in content:
                return ToolOutput(success=False, error="Text to replace not found in file")
            
            new_content = content.replace(input_data.old_text, input_data.new_text)
            target_path.write_text(new_content, encoding=input_data.encoding)
            
            return ToolOutput(success=True, data={
                "path": input_data.path,
                "replacements": content.count(input_data.old_text),
            })
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class RenameFileInput(ToolInputSchema):
    old_path: str
    new_path: str


class RenameFileTool(BaseTool):
    name = "rename_file"
    description = "Rename or move a file"
    permission_level = PermissionLevel.SAFE_LOCAL
    required_permissions = [Permission.FILE_WRITE]
    input_schema = RenameFileInput
    
    def _resolve_path(self, path: str) -> Path:
        base = Path(settings.DATA_DIR).resolve()
        target = (base / path).resolve()
        if not target.is_relative_to(base):
            raise ValueError("Path traversal attempt detected")
        return target
    
    async def execute(self, input_data: RenameFileInput) -> ToolOutput:
        try:
            old_path = self._resolve_path(input_data.old_path)
            new_path = self._resolve_path(input_data.new_path)
            
            if not old_path.exists():
                return ToolOutput(success=False, error=f"Source does not exist: {input_data.old_path}")
            
            if new_path.exists():
                return ToolOutput(success=False, error=f"Destination already exists: {input_data.new_path}")
            
            new_path.parent.mkdir(parents=True, exist_ok=True)
            old_path.rename(new_path)
            
            return ToolOutput(success=True, data={
                "old_path": input_data.old_path,
                "new_path": input_data.new_path,
            })
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class MoveFileInput(ToolInputSchema):
    source: str
    destination: str
    overwrite: bool = Field(default=False)


class MoveFileTool(BaseTool):
    name = "move_file"
    description = "Move a file or directory"
    permission_level = PermissionLevel.SAFE_LOCAL
    required_permissions = [Permission.FILE_WRITE]
    input_schema = MoveFileInput
    
    def _resolve_path(self, path: str) -> Path:
        base = Path(settings.DATA_DIR).resolve()
        target = (base / path).resolve()
        if not target.is_relative_to(base):
            raise ValueError("Path traversal attempt detected")
        return target
    
    async def execute(self, input_data: MoveFileInput) -> ToolOutput:
        try:
            source = self._resolve_path(input_data.source)
            dest = self._resolve_path(input_data.destination)
            
            if not source.exists():
                return ToolOutput(success=False, error=f"Source does not exist: {input_data.source}")
            
            if dest.exists() and not input_data.overwrite:
                return ToolOutput(success=False, error=f"Destination already exists: {input_data.destination}")
            
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(dest))
            
            return ToolOutput(success=True, data={
                "source": input_data.source,
                "destination": input_data.destination,
            })
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class CopyFileInput(ToolInputSchema):
    source: str
    destination: str
    overwrite: bool = Field(default=False)


class CopyFileTool(BaseTool):
    name = "copy_file"
    description = "Copy a file or directory"
    permission_level = PermissionLevel.SAFE_LOCAL
    required_permissions = [Permission.FILE_WRITE]
    input_schema = CopyFileInput
    
    def _resolve_path(self, path: str) -> Path:
        base = Path(settings.DATA_DIR).resolve()
        target = (base / path).resolve()
        if not target.is_relative_to(base):
            raise ValueError("Path traversal attempt detected")
        return target
    
    async def execute(self, input_data: CopyFileInput) -> ToolOutput:
        try:
            source = self._resolve_path(input_data.source)
            dest = self._resolve_path(input_data.destination)
            
            if not source.exists():
                return ToolOutput(success=False, error=f"Source does not exist: {input_data.source}")
            
            if dest.exists() and not input_data.overwrite:
                return ToolOutput(success=False, error=f"Destination already exists: {input_data.destination}")
            
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            if source.is_dir():
                shutil.copytree(str(source), str(dest))
            else:
                shutil.copy2(str(source), str(dest))
            
            return ToolOutput(success=True, data={
                "source": input_data.source,
                "destination": input_data.destination,
            })
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class DeleteFileInput(ToolInputSchema):
    path: str
    recursive: bool = Field(default=False)
    confirm: bool = Field(default=False)


class DeleteFileTool(BaseTool):
    name = "delete_file"
    description = "Delete a file or directory"
    permission_level = PermissionLevel.DANGEROUS
    required_permissions = [Permission.FILE_DELETE]
    input_schema = DeleteFileInput
    
    def _resolve_path(self, path: str) -> Path:
        base = Path(settings.DATA_DIR).resolve()
        target = (base / path).resolve()
        if not target.is_relative_to(base):
            raise ValueError("Path traversal attempt detected")
        return target
    
    async def execute(self, input_data: DeleteFileInput) -> ToolOutput:
        try:
            target_path = self._resolve_path(input_data.path)
            
            if not target_path.exists():
                return ToolOutput(success=False, error=f"Path does not exist: {input_data.path}")
            
            if target_path.is_dir() and not input_data.recursive:
                return ToolOutput(success=False, error="Directory not empty. Use recursive=true to delete.")
            
            if target_path.is_dir():
                shutil.rmtree(target_path)
            else:
                target_path.unlink()
            
            return ToolOutput(success=True, data={"path": input_data.path})
        except Exception as e:
            return ToolOutput(success=False, error=str(e))