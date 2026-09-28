from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime

from app.database.session import get_db_session
from app.database.models import Task, TaskStep, ToolCall, Approval, TaskStatus, ApprovalStatus
from app.security.dependencies import get_current_user
from app.agent.orchestrator import TaskExecutor, AgentContext
from app.main import agent_orchestrator


router = APIRouter()


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    conversation_id: Optional[str] = None


class TaskResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    status: str
    progress: int
    current_step: int
    total_steps: int
    result: Optional[str]
    error: Optional[str]
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(
    request: TaskCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    task = Task(
        user_id=current_user.id,
        conversation_id=request.conversation_id,
        title=request.title,
        description=request.description,
        status=TaskStatus.QUEUED,
    )
    db.add(task)
    await db.flush()
    await db.commit()
    
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status.value,
        progress=task.progress,
        current_step=task.current_step,
        total_steps=task.total_steps,
        result=task.result,
        error=task.error,
        created_at=task.created_at.isoformat(),
        started_at=task.started_at.isoformat() if task.started_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
    )


@router.post("/{task_id}/execute")
async def execute_task(
    task_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    if not agent_orchestrator:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == current_user.id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status not in [TaskStatus.QUEUED, TaskStatus.FAILED]:
        raise HTTPException(status_code=400, detail="Task cannot be executed")
    
    executor = TaskExecutor(agent_orchestrator)
    context = AgentContext(user_id=current_user.id, task_id=task.id)
    
    task = await executor.execute_task(task, context, db)
    await db.commit()
    
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status.value,
        progress=task.progress,
        current_step=task.current_step,
        total_steps=task.total_steps,
        result=task.result,
        error=task.error,
        created_at=task.created_at.isoformat(),
        started_at=task.started_at.isoformat() if task.started_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
    )


@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    status: Optional[str] = None,
    limit: int = 50,
):
    query = select(Task).where(Task.user_id == current_user.id)
    if status:
        query = query.where(Task.status == TaskStatus(status))
    query = query.order_by(desc(Task.created_at)).limit(limit)
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    return [
        TaskResponse(
            id=t.id,
            title=t.title,
            description=t.description,
            status=t.status.value,
            progress=t.progress,
            current_step=t.current_step,
            total_steps=t.total_steps,
            result=t.result,
            error=t.error,
            created_at=t.created_at.isoformat(),
            started_at=t.started_at.isoformat() if t.started_at else None,
            completed_at=t.completed_at.isoformat() if t.completed_at else None,
        )
        for t in tasks
    ]


@router.get("/{task_id}")
async def get_task(
    task_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == current_user.id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    steps_result = await db.execute(
        select(TaskStep).where(TaskStep.task_id == task_id).order_by(TaskStep.step_number)
    )
    steps = steps_result.scalars().all()
    
    tool_calls_result = await db.execute(
        select(ToolCall).where(ToolCall.task_id == task_id)
    )
    tool_calls = tool_calls_result.scalars().all()
    
    approvals_result = await db.execute(
        select(Approval).where(Approval.task_id == task_id)
    )
    approvals = approvals_result.scalars().all()
    
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status.value,
        "progress": task.progress,
        "current_step": task.current_step,
        "total_steps": task.total_steps,
        "plan": task.plan,
        "result": task.result,
        "error": task.error,
        "created_at": task.created_at.isoformat(),
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "steps": [
            {
                "id": s.id,
                "step_number": s.step_number,
                "tool_name": s.tool_name,
                "description": s.description,
                "input_args": s.input_args,
                "output_result": s.output_result,
                "error": s.error,
                "status": s.status,
                "started_at": s.started_at.isoformat() if s.started_at else None,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            }
            for s in steps
        ],
        "tool_calls": [
            {
                "id": tc.id,
                "tool_name": tc.tool_name,
                "input_args": tc.input_args,
                "output_result": tc.output_result,
                "error": tc.error,
                "permission_level": tc.permission_level.value,
                "approval_required": tc.approval_required,
                "execution_time_ms": tc.execution_time_ms,
                "created_at": tc.created_at.isoformat(),
            }
            for tc in tool_calls
        ],
        "approvals": [
            {
                "id": a.id,
                "title": a.title,
                "description": a.description,
                "permission_level": a.permission_level.value,
                "status": a.status.value,
                "expires_at": a.expires_at.isoformat(),
                "responded_at": a.responded_at.isoformat() if a.responded_at else None,
            }
            for a in approvals
        ],
    }


@router.post("/{task_id}/approve/{approval_id}")
async def approve_task(
    task_id: str,
    approval_id: str,
    approved: bool = True,
    reason: Optional[str] = None,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(Approval).where(
            Approval.id == approval_id,
            Approval.task_id == task_id,
            Approval.user_id == current_user.id,
        )
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    if approval.status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=400, detail="Approval already processed")
    
    approval.status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
    approval.responded_at = datetime.utcnow()
    approval.response_reason = reason
    
    if approved:
        from app.main import agent_orchestrator
        if agent_orchestrator:
            task_result = await db.execute(
                select(Task).where(Task.id == task_id)
            )
            task = task_result.scalar_one_or_none()
            if task:
                executor = TaskExecutor(agent_orchestrator)
                context = AgentContext(user_id=current_user.id, task_id=task.id)
                task = await executor.execute_task(task, context, db)
    else:
        task_result = await db.execute(select(Task).where(Task.id == task_id))
        task = task_result.scalar_one_or_none()
        if task:
            task.status = TaskStatus.CANCELLED
            task.error = "Approval rejected"
            task.completed_at = datetime.utcnow()
    
    await db.commit()
    return {"message": "Approved" if approved else "Rejected"}


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == current_user.id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    await db.delete(task)
    await db.commit()
    return {"message": "Task deleted"}