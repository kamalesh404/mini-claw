from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.security.dependencies import get_current_user, get_user_permissions
from app.tools.registry import tool_registry
from app.security.permissions import check_tool_permission


router = APIRouter()


class InspectRepositoryRequest(BaseModel):
    owner: str
    repo: str


class ListIssuesRequest(BaseModel):
    owner: str
    repo: str
    state: str = "open"
    labels: Optional[List[str]] = None
    limit: int = 30


class CreateIssueRequest(BaseModel):
    owner: str
    repo: str
    title: str
    body: Optional[str] = None
    labels: Optional[List[str]] = None
    assignees: Optional[List[str]] = None


class CommentIssueRequest(BaseModel):
    owner: str
    repo: str
    issue_number: int
    body: str


class ListPullRequestsRequest(BaseModel):
    owner: str
    repo: str
    state: str = "open"
    limit: int = 30


class CreateBranchRequest(BaseModel):
    owner: str
    repo: str
    branch_name: str
    from_branch: str = "main"


class CreateCommitRequest(BaseModel):
    owner: str
    repo: str
    branch: str
    message: str
    files: Dict[str, str]


class CreatePullRequestRequest(BaseModel):
    owner: str
    repo: str
    title: str
    body: Optional[str] = None
    head: str
    base: str = "main"
    draft: bool = False


class TriggerWorkflowRequest(BaseModel):
    owner: str
    repo: str
    workflow_id: str
    ref: str = "main"
    inputs: Optional[Dict[str, Any]] = None


class InspectWorkflowRequest(BaseModel):
    owner: str
    repo: str
    run_id: int


class DownloadArtifactRequest(BaseModel):
    owner: str
    repo: str
    artifact_id: int
    path: str = "."


@router.post("/repository")
async def inspect_repository(
    request: InspectRepositoryRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("inspect_repository", request.model_dump(), user_permissions)


@router.post("/issues")
async def list_issues(
    request: ListIssuesRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("list_issues", request.model_dump(), user_permissions)


@router.post("/issues/inspect")
async def inspect_issue(
    request: InspectIssueRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("inspect_issue", request.model_dump(), user_permissions)


class InspectIssueRequest(BaseModel):
    owner: str
    repo: str
    issue_number: int


@router.post("/issues/create")
async def create_issue(
    request: CreateIssueRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("create_issue", request.model_dump(), user_permissions)


@router.post("/issues/comment")
async def comment_issue(
    request: CommentIssueRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("comment_issue", request.model_dump(), user_permissions)


@router.post("/pull-requests")
async def list_pull_requests(
    request: ListPullRequestsRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("list_pull_requests", request.model_dump(), user_permissions)


@router.post("/pull-requests/inspect")
async def inspect_pull_request(
    request: InspectPullRequestRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("inspect_pull_request", request.model_dump(), user_permissions)


class InspectPullRequestRequest(BaseModel):
    owner: str
    repo: str
    pr_number: int


@router.post("/branches/create")
async def create_branch(
    request: CreateBranchRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("create_branch", request.model_dump(), user_permissions)


@router.post("/commits/create")
async def create_commit(
    request: CreateCommitRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("create_commit", request.model_dump(), user_permissions)


@router.post("/pull-requests/create")
async def create_pull_request(
    request: CreatePullRequestRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("create_pull_request", request.model_dump(), user_permissions)


@router.post("/workflows/trigger")
async def trigger_workflow(
    request: TriggerWorkflowRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("trigger_workflow", request.model_dump(), user_permissions)


@router.post("/workflows/inspect")
async def inspect_workflow(
    request: InspectWorkflowRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("inspect_workflow", request.model_dump(), user_permissions)


@router.post("/artifacts/download")
async def download_artifact(
    request: DownloadArtifactRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    user_permissions = get_user_permissions(current_user)
    return await _execute_tool("download_artifact", request.model_dump(), user_permissions)


async def _execute_tool(tool_name: str, args: dict, permissions):
    tool = tool_registry.get(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    if not check_tool_permission(permissions, tool_name):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    output = await tool_registry.execute_tool(tool_name, args, permissions)
    if not output.success:
        raise HTTPException(status_code=500, detail=output.error)
    return output.data