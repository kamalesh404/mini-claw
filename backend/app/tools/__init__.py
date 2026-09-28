from app.tools.registry import tool_registry
from app.tools.system_tools import (
    GetSystemInfoTool,
    GetCPUUsageTool,
    GetGPUUsageTool,
    GetRAMUsageTool,
    GetDiskUsageTool,
    GetNetworkInfoTool,
    ListProcessesTool,
    GetBatteryStatusTool,
)
from app.tools.file_tools import (
    ListFilesTool,
    SearchFilesTool,
    ReadFileTool,
    CreateFileTool,
    EditFileTool,
    RenameFileTool,
    MoveFileTool,
    CopyFileTool,
    DeleteFileTool,
)
from app.tools.terminal_tools import (
    RunCommandTool,
    RunPowerShellTool,
    RunPythonTool,
    RunGitTool,
    RunNpmTool,
    RunFlutterTool,
    RunDockerTool,
)
from app.tools.app_tools import (
    OpenApplicationTool,
    CloseApplicationTool,
    LaunchURLTool,
)
from app.tools.dev_tools import (
    InspectProjectTool,
    InstallDependenciesTool,
    RunTestsTool,
    RunLinterTool,
    BuildProjectTool,
    InspectGitStatusTool,
    CreateGitBranchTool,
    CommitChangesTool,
)


def register_core_tools() -> None:
    tools = [
        GetSystemInfoTool(),
        GetCPUUsageTool(),
        GetGPUUsageTool(),
        GetRAMUsageTool(),
        GetDiskUsageTool(),
        GetNetworkInfoTool(),
        ListProcessesTool(),
        GetBatteryStatusTool(),
        ListFilesTool(),
        SearchFilesTool(),
        ReadFileTool(),
        CreateFileTool(),
        EditFileTool(),
        RenameFileTool(),
        MoveFileTool(),
        CopyFileTool(),
        DeleteFileTool(),
        RunCommandTool(),
        RunPowerShellTool(),
        RunPythonTool(),
        RunGitTool(),
        RunNpmTool(),
        RunFlutterTool(),
        RunDockerTool(),
        OpenApplicationTool(),
        CloseApplicationTool(),
        LaunchURLTool(),
        InspectProjectTool(),
        InstallDependenciesTool(),
        RunTestsTool(),
        RunLinterTool(),
        BuildProjectTool(),
        InspectGitStatusTool(),
        CreateGitBranchTool(),
        CommitChangesTool(),
    ]
    
    for tool in tools:
        tool_registry.register(tool)


def register_github_tools(github_client) -> None:
    from app.tools.github_tools import (
        InspectRepositoryTool,
        ListIssuesTool,
        InspectIssueTool,
        CreateIssueTool,
        CommentIssueTool,
        ListPullRequestsTool,
        InspectPullRequestTool,
        CreateBranchTool,
        CreateCommitTool,
        CreatePullRequestTool,
        TriggerWorkflowTool,
        InspectWorkflowTool,
        DownloadArtifactTool,
    )
    
    tools = [
        InspectRepositoryTool(github_client),
        ListIssuesTool(github_client),
        InspectIssueTool(github_client),
        CreateIssueTool(github_client),
        CommentIssueTool(github_client),
        ListPullRequestsTool(github_client),
        InspectPullRequestTool(github_client),
        CreateBranchTool(github_client),
        CreateCommitTool(github_client),
        CreatePullRequestTool(github_client),
        TriggerWorkflowTool(github_client),
        InspectWorkflowTool(github_client),
        DownloadArtifactTool(github_client),
    ]
    
    for tool in tools:
        tool_registry.register(tool)


def register_browser_tools(browser_manager) -> None:
    from app.tools.browser_tools import (
        OpenPageTool,
        NavigateTool,
        ExtractPageTextTool,
        TakeScreenshotTool,
        ClickElementTool,
        FillFormTool,
        ClosePageTool,
    )
    
    tools = [
        OpenPageTool(browser_manager),
        NavigateTool(browser_manager),
        ExtractPageTextTool(browser_manager),
        TakeScreenshotTool(browser_manager),
        ClickElementTool(browser_manager),
        FillFormTool(browser_manager),
        ClosePageTool(browser_manager),
    ]
    
    for tool in tools:
        tool_registry.register(tool)


def register_scheduler_tools(scheduler) -> None:
    from app.tools.scheduler_tools import (
        CreateTaskTool,
        UpdateTaskTool,
        DeleteTaskTool,
        ListTasksTool,
        RunTaskNowTool,
    )
    
    tools = [
        CreateTaskTool(scheduler),
        UpdateTaskTool(scheduler),
        DeleteTaskTool(scheduler),
        ListTasksTool(scheduler),
        RunTaskNowTool(scheduler),
    ]
    
    for tool in tools:
        tool_registry.register(tool)


def register_notification_tools(notification_service) -> None:
    from app.tools.notification_tools import (
        SendMobileNotificationTool,
        SendEmailTool,
        SendWebNotificationTool,
    )
    
    tools = [
        SendMobileNotificationTool(notification_service),
        SendEmailTool(notification_service),
        SendWebNotificationTool(notification_service),
    ]
    
    for tool in tools:
        tool_registry.register(tool)