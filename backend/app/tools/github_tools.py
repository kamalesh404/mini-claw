from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.tools.registry import BaseTool, ToolInputSchema, ToolOutput, PermissionLevel
from app.security.permissions import Permission
from app.integrations.github.client import GitHubClient


class GitHubToolBase(BaseTool):
    permission_level = PermissionLevel.READ_ONLY
    required_permissions = [Permission.GITHUB_READ]
    
    def __init__(self, github_client: GitHubClient):
        super().__init__()
        self.github = github_client


class InspectRepositoryInput(ToolInputSchema):
    owner: str
    repo: str


class InspectRepositoryTool(GitHubToolBase):
    name = "inspect_repository"
    description = "Get repository information"
    input_schema = InspectRepositoryInput
    
    async def execute(self, input_data: InspectRepositoryInput) -> ToolOutput:
        try:
            repo = await self.github.get_repository(input_data.owner, input_data.repo)
            return ToolOutput(success=True, data=repo)
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class ListIssuesInput(ToolInputSchema):
    owner: str
    repo: str
    state: str = Field(default="open", pattern="^(open|closed|all)$")
    labels: Optional[List[str]] = Field(default=None)
    limit: int = Field(default=30, ge=1, le=100)


class ListIssuesTool(GitHubToolBase):
    name = "list_issues"
    description = "List repository issues"
    input_schema = ListIssuesInput
    
    async def execute(self, input_data: ListIssuesInput) -> ToolOutput:
        try:
            issues = await self.github.list_issues(
                input_data.owner,
                input_data.repo,
                state=input_data.state,
                labels=input_data.labels,
                limit=input_data.limit,
            )
            return ToolOutput(success=True, data={"issues": issues})
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class InspectIssueInput(ToolInputSchema):
    owner: str
    repo: str
    issue_number: int


class InspectIssueTool(GitHubToolBase):
    name = "inspect_issue"
    description = "Get detailed issue information"
    input_schema = InspectIssueInput
    
    async def execute(self, input_data: InspectIssueInput) -> ToolOutput:
        try:
            issue = await self.github.get_issue(input_data.owner, input_data.repo, input_data.issue_number)
            return ToolOutput(success=True, data=issue)
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class CreateIssueInput(ToolInputSchema):
    owner: str
    repo: str
    title: str
    body: Optional[str] = Field(default=None)
    labels: Optional[List[str]] = Field(default=None)
    assignees: Optional[List[str]] = Field(default=None)


class CreateIssueTool(GitHubToolBase):
    name = "create_issue"
    description = "Create a new issue"
    permission_level = PermissionLevel.DEVELOPER
    required_permissions = [Permission.GITHUB_WRITE]
    input_schema = CreateIssueInput
    
    async def execute(self, input_data: CreateIssueInput) -> ToolOutput:
        try:
            issue = await self.github.create_issue(
                input_data.owner,
                input_data.repo,
                input_data.title,
                input_data.body,
                input_data.labels,
                input_data.assignees,
            )
            return ToolOutput(success=True, data=issue)
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class CommentIssueInput(ToolInputSchema):
    owner: str
    repo: str
    issue_number: int
    body: str


class CommentIssueTool(GitHubToolBase):
    name = "comment_issue"
    description = "Add a comment to an issue"
    permission_level = PermissionLevel.DEVELOPER
    required_permissions = [Permission.GITHUB_WRITE]
    input_schema = CommentIssueInput
    
    async def execute(self, input_data: CommentIssueInput) -> ToolOutput:
        try:
            comment = await self.github.create_issue_comment(
                input_data.owner,
                input_data.repo,
                input_data.issue_number,
                input_data.body,
            )
            return ToolOutput(success=True, data=comment)
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class ListPullRequestsInput(ToolInputSchema):
    owner: str
    repo: str
    state: str = Field(default="open", pattern="^(open|closed|all)$")
    limit: int = Field(default=30, ge=1, le=100)


class ListPullRequestsTool(GitHubToolBase):
    name = "list_pull_requests"
    description = "List pull requests"
    input_schema = ListPullRequestsInput
    
    async def execute(self, input_data: ListPullRequestsInput) -> ToolOutput:
        try:
            prs = await self.github.list_pull_requests(
                input_data.owner,
                input_data.repo,
                state=input_data.state,
                limit=input_data.limit,
            )
            return ToolOutput(success=True, data={"pull_requests": prs})
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class InspectPullRequestInput(ToolInputSchema):
    owner: str
    repo: str
    pr_number: int


class InspectPullRequestTool(GitHubToolBase):
    name = "inspect_pull_request"
    description = "Get detailed pull request information"
    input_schema = InspectPullRequestInput
    
    async def execute(self, input_data: InspectPullRequestInput) -> ToolOutput:
        try:
            pr = await self.github.get_pull_request(input_data.owner, input_data.repo, input_data.pr_number)
            return ToolOutput(success=True, data=pr)
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class CreateBranchInput(ToolInputSchema):
    owner: str
    repo: str
    branch_name: str
    from_branch: str = Field(default="main")


class CreateBranchTool(GitHubToolBase):
    name = "create_branch"
    description = "Create a new branch"
    permission_level = PermissionLevel.DEVELOPER
    required_permissions = [Permission.GITHUB_WRITE]
    input_schema = CreateBranchInput
    
    async def execute(self, input_data: CreateBranchInput) -> ToolOutput:
        try:
            branch = await self.github.create_branch(
                input_data.owner,
                input_data.repo,
                input_data.branch_name,
                input_data.from_branch,
            )
            return ToolOutput(success=True, data=branch)
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class CreateCommitInput(ToolInputSchema):
    owner: str
    repo: str
    branch: str
    message: str
    files: Dict[str, str]  # path -> content


class CreateCommitTool(GitHubToolBase):
    name = "create_commit"
    description = "Create a commit with file changes"
    permission_level = PermissionLevel.DEVELOPER
    required_permissions = [Permission.GITHUB_WRITE]
    input_schema = CreateCommitInput
    
    async def execute(self, input_data: CreateCommitInput) -> ToolOutput:
        try:
            commit = await self.github.create_commit(
                input_data.owner,
                input_data.repo,
                input_data.branch,
                input_data.message,
                input_data.files,
            )
            return ToolOutput(success=True, data=commit)
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class CreatePullRequestInput(ToolInputSchema):
    owner: str
    repo: str
    title: str
    body: Optional[str] = Field(default=None)
    head: str
    base: str = Field(default="main")
    draft: bool = Field(default=False)


class CreatePullRequestTool(GitHubToolBase):
    name = "create_pull_request"
    description = "Create a pull request"
    permission_level = PermissionLevel.DEVELOPER
    required_permissions = [Permission.GITHUB_WRITE]
    input_schema = CreatePullRequestInput
    
    async def execute(self, input_data: CreatePullRequestInput) -> ToolOutput:
        try:
            pr = await self.github.create_pull_request(
                input_data.owner,
                input_data.repo,
                input_data.title,
                input_data.body,
                input_data.head,
                input_data.base,
                input_data.draft,
            )
            return ToolOutput(success=True, data=pr)
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class TriggerWorkflowInput(ToolInputSchema):
    owner: str
    repo: str
    workflow_id: str
    ref: str = Field(default="main")
    inputs: Optional[Dict[str, Any]] = Field(default=None)


class TriggerWorkflowTool(GitHubToolBase):
    name = "trigger_workflow"
    description = "Trigger a GitHub Actions workflow"
    permission_level = PermissionLevel.DEVELOPER
    required_permissions = [Permission.GITHUB_WRITE]
    input_schema = TriggerWorkflowInput
    
    async def execute(self, input_data: TriggerWorkflowInput) -> ToolOutput:
        try:
            run = await self.github.trigger_workflow(
                input_data.owner,
                input_data.repo,
                input_data.workflow_id,
                input_data.ref,
                input_data.inputs,
            )
            return ToolOutput(success=True, data=run)
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class InspectWorkflowInput(ToolInputSchema):
    owner: str
    repo: str
    run_id: int


class InspectWorkflowTool(GitHubToolBase):
    name = "inspect_workflow"
    description = "Get workflow run details"
    input_schema = InspectWorkflowInput
    
    async def execute(self, input_data: InspectWorkflowInput) -> ToolOutput:
        try:
            run = await self.github.get_workflow_run(input_data.owner, input_data.repo, input_data.run_id)
            return ToolOutput(success=True, data=run)
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class DownloadArtifactInput(ToolInputSchema):
    owner: str
    repo: str
    artifact_id: int
    path: str = Field(default=".")


class DownloadArtifactTool(GitHubToolBase):
    name = "download_artifact"
    description = "Download a workflow artifact"
    permission_level = PermissionLevel.DEVELOPER
    required_permissions = [Permission.GITHUB_WRITE]
    input_schema = DownloadArtifactInput
    
    async def execute(self, input_data: DownloadArtifactInput) -> ToolOutput:
        try:
            result = await self.github.download_artifact(
                input_data.owner,
                input_data.repo,
                input_data.artifact_id,
                input_data.path,
            )
            return ToolOutput(success=True, data=result)
        except Exception as e:
            return ToolOutput(success=False, error=str(e))