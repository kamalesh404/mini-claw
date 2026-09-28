from typing import List, Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from uuid import uuid4
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Automation, Event
from app.tools.registry import tool_registry
from app.config import settings


class SchedulerManager:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.action_handlers: Dict[str, Callable] = {}
        self._running = False
    
    def start(self):
        if not self._running:
            self.scheduler.start()
            self._running = True
    
    def shutdown(self):
        if self._running:
            self.scheduler.shutdown()
            self._running = False
    
    def register_action(self, action_type: str, handler: Callable):
        self.action_handlers[action_type] = handler
    
    async def create_task(
        self,
        db: AsyncSession,
        user_id: str,
        name: str,
        trigger_type: str,
        trigger_config: Dict[str, Any],
        action_type: str,
        action_config: Dict[str, Any],
        conditions: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        if trigger_type not in ["cron", "interval", "date", "event"]:
            raise ValueError(f"Invalid trigger type: {trigger_type}")
        
        if action_type not in self.action_handlers:
            raise ValueError(f"Unknown action type: {action_type}")
        
        automation = Automation(
            id=str(uuid4()),
            user_id=user_id,
            name=name,
            trigger_type=trigger_type,
            trigger_config=trigger_config,
            action_type=action_type,
            action_config=action_config,
            conditions=conditions or [],
            is_enabled=True,
        )
        
        db.add(automation)
        await db.flush()
        
        await self._schedule_automation(automation)
        
        return automation.id
    
    async def _schedule_automation(self, automation: Automation):
        trigger = self._create_trigger(automation)
        if not trigger:
            return
        
        job_id = f"automation_{automation.id}"
        
        self.scheduler.add_job(
            self._execute_automation,
            trigger=trigger,
            id=job_id,
            args=[automation.id],
            replace_existing=True,
        )
        
        if automation.trigger_type == "cron":
            next_run = trigger.get_next_fire_time(None, datetime.utcnow())
            automation.next_run_at = next_run
    
    def _create_trigger(self, automation: Automation):
        config = automation.trigger_config
        
        if automation.trigger_type == "cron":
            return CronTrigger.from_crontab(config.get("expression", "0 * * * *"))
        elif automation.trigger_type == "interval":
            return IntervalTrigger(
                seconds=config.get("seconds", 0),
                minutes=config.get("minutes", 0),
                hours=config.get("hours", 0),
                days=config.get("days", 0),
            )
        elif automation.trigger_type == "date":
            run_date = config.get("run_date")
            if run_date:
                return DateTrigger(run_date=run_date)
        
        return None
    
    async def _execute_automation(self, automation_id: str):
        from app.database.session import get_session
        
        async with get_session() as db:
            result = await db.execute(
                select(Automation).where(Automation.id == automation_id)
            )
            automation = result.scalar_one_or_none()
            
            if not automation or not automation.is_enabled:
                return
            
            if not self._check_conditions(automation.conditions):
                return
            
            handler = self.action_handlers.get(automation.action_type)
            if not handler:
                return
            
            try:
                await handler(automation.action_config)
                automation.last_run_at = datetime.utcnow()
                automation.run_count += 1
                automation.success_count += 1
            except Exception as e:
                automation.last_error = str(e)
                automation.failure_count += 1
            
            if automation.trigger_type == "cron":
                trigger = self._create_trigger(automation)
                if trigger:
                    next_run = trigger.get_next_fire_time(None, datetime.utcnow())
                    automation.next_run_at = next_run
            
            await db.commit()
    
    def _check_conditions(self, conditions: Optional[List[Dict[str, Any]]]) -> bool:
        if not conditions:
            return True
        
        for condition in conditions:
            if not self._evaluate_condition(condition):
                return False
        return True
    
    def _evaluate_condition(self, condition: Dict[str, Any]) -> bool:
        condition_type = condition.get("type")
        
        if condition_type == "time_range":
            now = datetime.utcnow().time()
            start = condition.get("start")
            end = condition.get("end")
            if start and end:
                from datetime import time
                start_time = time.fromisoformat(start)
                end_time = time.fromisoformat(end)
                return start_time <= now <= end_time
        
        return True
    
    async def update_task(
        self,
        db: AsyncSession,
        task_id: str,
        name: Optional[str] = None,
        trigger_config: Optional[Dict[str, Any]] = None,
        action_config: Optional[Dict[str, Any]] = None,
        conditions: Optional[List[Dict[str, Any]]] = None,
        is_enabled: Optional[bool] = None,
    ) -> bool:
        result = await db.execute(select(Automation).where(Automation.id == task_id))
        automation = result.scalar_one_or_none()
        
        if not automation:
            return False
        
        if name is not None:
            automation.name = name
        if trigger_config is not None:
            automation.trigger_config = trigger_config
        if action_config is not None:
            automation.action_config = action_config
        if conditions is not None:
            automation.conditions = conditions
        if is_enabled is not None:
            automation.is_enabled = is_enabled
        
        automation.updated_at = datetime.utcnow()
        
        await self._schedule_automation(automation)
        
        return True
    
    async def delete_task(self, db: AsyncSession, task_id: str) -> bool:
        result = await db.execute(select(Automation).where(Automation.id == task_id))
        automation = result.scalar_one_or_none()
        
        if not automation:
            return False
        
        job_id = f"automation_{task_id}"
        try:
            self.scheduler.remove_job(job_id)
        except Exception:
            pass
        
        await db.delete(automation)
        return True
    
    async def list_tasks(
        self,
        db: AsyncSession,
        user_id: str,
        enabled_only: bool = False,
    ) -> List[Dict[str, Any]]:
        query = select(Automation).where(Automation.user_id == user_id)
        if enabled_only:
            query = query.where(Automation.is_enabled == True)
        
        result = await db.execute(query)
        automations = result.scalars().all()
        
        return [
            {
                "id": a.id,
                "name": a.name,
                "trigger_type": a.trigger_type,
                "trigger_config": a.trigger_config,
                "action_type": a.action_type,
                "action_config": a.action_config,
                "conditions": a.conditions,
                "is_enabled": a.is_enabled,
                "last_run_at": a.last_run_at.isoformat() if a.last_run_at else None,
                "next_run_at": a.next_run_at.isoformat() if a.next_run_at else None,
                "run_count": a.run_count,
                "success_count": a.success_count,
                "failure_count": a.failure_count,
                "last_error": a.last_error,
            }
            for a in automations
        ]
    
    async def run_task_now(self, db: AsyncSession, task_id: str) -> Dict[str, Any]:
        result = await db.execute(select(Automation).where(Automation.id == task_id))
        automation = result.scalar_one_or_none()
        
        if not automation:
            return {"success": False, "error": "Task not found"}
        
        handler = self.action_handlers.get(automation.action_type)
        if not handler:
            return {"success": False, "error": "Action handler not found"}
        
        try:
            await handler(automation.action_config)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def emit_event(self, event_type: str, source: str, payload: Dict[str, Any], user_id: Optional[str] = None):
        from app.database.session import get_session
        
        async with get_session() as db:
            event = Event(
                id=str(uuid4()),
                event_type=event_type,
                source=source,
                payload=payload,
                user_id=user_id,
            )
            db.add(event)
            await db.commit()
        
        for automation in await self._get_event_automations(event_type):
            if self._check_conditions(automation.conditions):
                handler = self.action_handlers.get(automation.action_type)
                if handler:
                    try:
                        await handler(automation.action_config)
                    except Exception:
                        pass
    
    async def _get_event_automations(self, event_type: str) -> List[Automation]:
        from app.database.session import get_session
        
        async with get_session() as db:
            result = await db.execute(
                select(Automation).where(
                    and_(
                        Automation.trigger_type == "event",
                        Automation.trigger_config["event_type"].astext == event_type,
                        Automation.is_enabled == True,
                    )
                )
            )
            return list(result.scalars().all())


from sqlalchemy import and_