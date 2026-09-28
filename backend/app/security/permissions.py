from enum import Enum
from typing import Optional, Set
from dataclasses import dataclass, field

from app.database.models import PermissionLevel


class Permission(Enum):
    # System permissions
    SYSTEM_READ = "system:read"
    SYSTEM_WRITE = "system:write"
    SYSTEM_ADMIN = "system:admin"
    
    # File permissions
    FILE_READ = "file:read"
    FILE_WRITE = "file:write"
    FILE_DELETE = "file:delete"
    FILE_EXECUTE = "file:execute"
    
    # Terminal permissions
    TERMINAL_READ = "terminal:read"
    TERMINAL_EXECUTE = "terminal:execute"
    TERMINAL_ADMIN = "terminal:admin"
    
    # Application permissions
    APP_LAUNCH = "app:launch"
    APP_CLOSE = "app:close"
    APP_MANAGE = "app:manage"
    
    # Development permissions
    DEV_READ = "dev:read"
    DEV_WRITE = "dev:write"
    DEV_TEST = "dev:test"
    DEV_BUILD = "dev:build"
    DEV_DEPLOY = "dev:deploy"
    
    # Git permissions
    GIT_READ = "git:read"
    GIT_WRITE = "git:write"
    GIT_ADMIN = "git:admin"
    
    # GitHub permissions
    GITHUB_READ = "github:read"
    GITHUB_WRITE = "github:write"
    GITHUB_ADMIN = "github:admin"
    
    # Browser permissions
    BROWSER_READ = "browser:read"
    BROWSER_WRITE = "browser:write"
    BROWSER_ADMIN = "browser:admin"
    
    # Scheduler permissions
    SCHEDULER_READ = "scheduler:read"
    SCHEDULER_WRITE = "scheduler:write"
    SCHEDULER_ADMIN = "scheduler:admin"
    
    # Notification permissions
    NOTIFICATION_SEND = "notification:send"
    NOTIFICATION_MANAGE = "notification:manage"
    
    # Memory permissions
    MEMORY_READ = "memory:read"
    MEMORY_WRITE = "memory:write"
    MEMORY_DELETE = "memory:delete"
    
    # Automation permissions
    AUTOMATION_READ = "automation:read"
    AUTOMATION_WRITE = "automation:write"
    AUTOMATION_ADMIN = "automation:admin"


@dataclass
class PermissionSet:
    permissions: Set[Permission] = field(default_factory=set)
    
    def add(self, permission: Permission) -> None:
        self.permissions.add(permission)
    
    def remove(self, permission: Permission) -> None:
        self.permissions.discard(permission)
    
    def has(self, permission: Permission) -> bool:
        return permission in self.permissions
    
    def has_any(self, *permissions: Permission) -> bool:
        return any(p in self.permissions for p in permissions)
    
    def has_all(self, *permissions: Permission) -> bool:
        return all(p in self.permissions for p in permissions)


DEFAULT_PERMISSIONS_BY_LEVEL = {
    PermissionLevel.READ_ONLY: {
        Permission.SYSTEM_READ,
        Permission.FILE_READ,
        Permission.TERMINAL_READ,
        Permission.APP_LAUNCH,
        Permission.DEV_READ,
        Permission.DEV_TEST,
        Permission.GIT_READ,
        Permission.GITHUB_READ,
        Permission.BROWSER_READ,
        Permission.SCHEDULER_READ,
        Permission.MEMORY_READ,
        Permission.AUTOMATION_READ,
    },
    PermissionLevel.SAFE_LOCAL: {
        Permission.SYSTEM_READ,
        Permission.FILE_READ,
        Permission.FILE_WRITE,
        Permission.TERMINAL_READ,
        Permission.TERMINAL_EXECUTE,
        Permission.APP_LAUNCH,
        Permission.APP_CLOSE,
        Permission.DEV_READ,
        Permission.DEV_WRITE,
        Permission.DEV_TEST,
        Permission.DEV_BUILD,
        Permission.GIT_READ,
        Permission.GIT_WRITE,
        Permission.GITHUB_READ,
        Permission.GITHUB_WRITE,
        Permission.BROWSER_READ,
        Permission.BROWSER_WRITE,
        Permission.SCHEDULER_READ,
        Permission.SCHEDULER_WRITE,
        Permission.NOTIFICATION_SEND,
        Permission.MEMORY_READ,
        Permission.MEMORY_WRITE,
        Permission.AUTOMATION_READ,
        Permission.AUTOMATION_WRITE,
    },
    PermissionLevel.DEVELOPER: {
        Permission.SYSTEM_READ,
        Permission.SYSTEM_WRITE,
        Permission.FILE_READ,
        Permission.FILE_WRITE,
        Permission.FILE_DELETE,
        Permission.TERMINAL_READ,
        Permission.TERMINAL_EXECUTE,
        Permission.APP_LAUNCH,
        Permission.APP_CLOSE,
        Permission.APP_MANAGE,
        Permission.DEV_READ,
        Permission.DEV_WRITE,
        Permission.DEV_TEST,
        Permission.DEV_BUILD,
        Permission.DEV_DEPLOY,
        Permission.GIT_READ,
        Permission.GIT_WRITE,
        Permission.GIT_ADMIN,
        Permission.GITHUB_READ,
        Permission.GITHUB_WRITE,
        Permission.GITHUB_ADMIN,
        Permission.BROWSER_READ,
        Permission.BROWSER_WRITE,
        Permission.SCHEDULER_READ,
        Permission.SCHEDULER_WRITE,
        Permission.SCHEDULER_ADMIN,
        Permission.NOTIFICATION_SEND,
        Permission.NOTIFICATION_MANAGE,
        Permission.MEMORY_READ,
        Permission.MEMORY_WRITE,
        Permission.MEMORY_DELETE,
        Permission.AUTOMATION_READ,
        Permission.AUTOMATION_WRITE,
        Permission.AUTOMATION_ADMIN,
    },
    PermissionLevel.SYSTEM: {
        Permission.SYSTEM_READ,
        Permission.SYSTEM_WRITE,
        Permission.SYSTEM_ADMIN,
        Permission.FILE_READ,
        Permission.FILE_WRITE,
        Permission.FILE_DELETE,
        Permission.FILE_EXECUTE,
        Permission.TERMINAL_READ,
        Permission.TERMINAL_EXECUTE,
        Permission.TERMINAL_ADMIN,
        Permission.APP_LAUNCH,
        Permission.APP_CLOSE,
        Permission.APP_MANAGE,
        Permission.DEV_READ,
        Permission.DEV_WRITE,
        Permission.DEV_TEST,
        Permission.DEV_BUILD,
        Permission.DEV_DEPLOY,
        Permission.GIT_READ,
        Permission.GIT_WRITE,
        Permission.GIT_ADMIN,
        Permission.GITHUB_READ,
        Permission.GITHUB_WRITE,
        Permission.GITHUB_ADMIN,
        Permission.BROWSER_READ,
        Permission.BROWSER_WRITE,
        Permission.BROWSER_ADMIN,
        Permission.SCHEDULER_READ,
        Permission.SCHEDULER_WRITE,
        Permission.SCHEDULER_ADMIN,
        Permission.NOTIFICATION_SEND,
        Permission.NOTIFICATION_MANAGE,
        Permission.MEMORY_READ,
        Permission.MEMORY_WRITE,
        Permission.MEMORY_DELETE,
        Permission.AUTOMATION_READ,
        Permission.AUTOMATION_WRITE,
        Permission.AUTOMATION_ADMIN,
    },
    PermissionLevel.DANGEROUS: set(Permission),
}


TOOL_PERMISSION_MAP = {
    # System tools
    "get_system_info": PermissionLevel.READ_ONLY,
    "get_cpu_usage": PermissionLevel.READ_ONLY,
    "get_gpu_usage": PermissionLevel.READ_ONLY,
    "get_ram_usage": PermissionLevel.READ_ONLY,
    "get_disk_usage": PermissionLevel.READ_ONLY,
    "get_network_info": PermissionLevel.READ_ONLY,
    "list_processes": PermissionLevel.READ_ONLY,
    "get_battery_status": PermissionLevel.READ_ONLY,
    
    # File tools
    "list_files": PermissionLevel.READ_ONLY,
    "search_files": PermissionLevel.READ_ONLY,
    "read_file": PermissionLevel.READ_ONLY,
    "create_file": PermissionLevel.SAFE_LOCAL,
    "edit_file": PermissionLevel.SAFE_LOCAL,
    "rename_file": PermissionLevel.SAFE_LOCAL,
    "move_file": PermissionLevel.SAFE_LOCAL,
    "copy_file": PermissionLevel.SAFE_LOCAL,
    "delete_file": PermissionLevel.DANGEROUS,
    
    # Terminal tools
    "run_command": PermissionLevel.DEVELOPER,
    "run_powershell": PermissionLevel.DEVELOPER,
    "run_python": PermissionLevel.DEVELOPER,
    "run_git": PermissionLevel.DEVELOPER,
    "run_npm": PermissionLevel.DEVELOPER,
    "run_flutter": PermissionLevel.DEVELOPER,
    "run_docker": PermissionLevel.SYSTEM,
    
    # Application tools
    "open_application": PermissionLevel.SAFE_LOCAL,
    "close_application": PermissionLevel.SAFE_LOCAL,
    "launch_url": PermissionLevel.SAFE_LOCAL,
    
    # Development tools
    "inspect_project": PermissionLevel.READ_ONLY,
    "install_dependencies": PermissionLevel.DEVELOPER,
    "run_tests": PermissionLevel.READ_ONLY,
    "run_linter": PermissionLevel.READ_ONLY,
    "build_project": PermissionLevel.DEVELOPER,
    "inspect_git_status": PermissionLevel.READ_ONLY,
    "create_git_branch": PermissionLevel.DEVELOPER,
    "commit_changes": PermissionLevel.DEVELOPER,
    
    # GitHub tools
    "inspect_repository": PermissionLevel.READ_ONLY,
    "list_issues": PermissionLevel.READ_ONLY,
    "inspect_issue": PermissionLevel.READ_ONLY,
    "create_issue": PermissionLevel.DEVELOPER,
    "comment_issue": PermissionLevel.DEVELOPER,
    "list_pull_requests": PermissionLevel.READ_ONLY,
    "inspect_pull_request": PermissionLevel.READ_ONLY,
    "create_branch": PermissionLevel.DEVELOPER,
    "create_commit": PermissionLevel.DEVELOPER,
    "create_pull_request": PermissionLevel.DEVELOPER,
    "trigger_workflow": PermissionLevel.DEVELOPER,
    "inspect_workflow": PermissionLevel.READ_ONLY,
    "download_artifact": PermissionLevel.READ_ONLY,
    
    # Browser tools
    "open_page": PermissionLevel.SAFE_LOCAL,
    "navigate": PermissionLevel.SAFE_LOCAL,
    "extract_page_text": PermissionLevel.READ_ONLY,
    "take_screenshot": PermissionLevel.SAFE_LOCAL,
    
    # Scheduler tools
    "create_task": PermissionLevel.DEVELOPER,
    "update_task": PermissionLevel.DEVELOPER,
    "delete_task": PermissionLevel.DANGEROUS,
    "list_tasks": PermissionLevel.READ_ONLY,
    "run_task_now": PermissionLevel.DEVELOPER,
    
    # Notification tools
    "send_mobile_notification": PermissionLevel.SAFE_LOCAL,
    "send_email": PermissionLevel.DEVELOPER,
    "send_web_notification": PermissionLevel.SAFE_LOCAL,
}


def get_tool_permission_level(tool_name: str) -> PermissionLevel:
    return TOOL_PERMISSION_MAP.get(tool_name, PermissionLevel.DANGEROUS)


def get_permissions_for_level(level: PermissionLevel) -> Set[Permission]:
    return DEFAULT_PERMISSIONS_BY_LEVEL.get(level, set())


def check_permission(user_permissions: PermissionSet, required_permission: Permission) -> bool:
    return user_permissions.has(required_permission)


def check_tool_permission(user_permissions: PermissionSet, tool_name: str) -> bool:
    required_level = get_tool_permission_level(tool_name)
    required_permissions = get_permissions_for_level(required_level)
    return user_permissions.has_any(*required_permissions)