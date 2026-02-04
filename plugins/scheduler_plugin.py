"""
Scheduler Plugin - Provides cron-like scheduled tasks.
"""

import asyncio
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from core.event_bus import Event
from core.plugin_manager import BasePlugin


class SchedulerPlugin(BasePlugin):
    """
    Scheduler plugin using APScheduler for cron-like tasks.
    
    Config:
        tasks: List of scheduled task configurations.
        
    Example config:
        tasks:
          - name: "daily_greeting"
            cron: "0 9 * * *"
            event: "scheduled.daily_greeting"
            data: {"message": "Good morning!"}
    """
    
    def __init__(self, event_bus, config: Dict[str, Any]):
        super().__init__(event_bus, config)
        self._scheduler = None
        self._running = False
    
    async def on_load(self) -> None:
        """Initialize and start the scheduler."""
        try:
            from apscheduler.schedulers.asyncio import AsyncIOScheduler
            from apscheduler.triggers.cron import CronTrigger
            
            self._scheduler = AsyncIOScheduler()
            
            # Add configured tasks
            tasks = self.config.get("tasks", [])
            for task_config in tasks:
                self._add_task(task_config)
            
            # Start scheduler
            self._scheduler.start()
            self._running = True
            print(f"SchedulerPlugin loaded with {len(tasks)} tasks")
            
        except ImportError:
            print("APScheduler not installed. Run: pip install apscheduler")
            raise
    
    async def on_unload(self) -> None:
        """Shutdown the scheduler."""
        if self._scheduler and self._running:
            self._scheduler.shutdown()
            self._running = False
    
    def _add_task(self, task_config: Dict[str, Any]) -> None:
        """Add a scheduled task from config."""
        from apscheduler.triggers.cron import CronTrigger
        
        name = task_config.get("name", "unnamed")
        cron_expr = task_config.get("cron")
        event_name = task_config.get("event", f"scheduled.{name}")
        data = task_config.get("data", {})
        
        if not cron_expr:
            print(f"Skipping task {name}: no cron expression")
            return
        
        # Parse cron expression (minute hour day month day_of_week)
        parts = cron_expr.split()
        if len(parts) == 5:
            trigger = CronTrigger(
                minute=parts[0],
                hour=parts[1],
                day=parts[2],
                month=parts[3],
                day_of_week=parts[4]
            )
        else:
            print(f"Invalid cron expression for {name}: {cron_expr}")
            return
        
        # Create async wrapper for the job
        async def job_wrapper():
            await self.publish(event_name, {
                "task_name": name,
                "triggered_at": datetime.now().isoformat(),
                **data
            })
        
        def sync_wrapper():
            asyncio.create_task(job_wrapper())
        
        self._scheduler.add_job(sync_wrapper, trigger, id=name, replace_existing=True)
        print(f"Scheduled task: {name} ({cron_expr})")
    
    def add_task_runtime(
        self,
        name: str,
        cron: str,
        event_name: str,
        data: Dict[str, Any] = None
    ) -> None:
        """Add a task at runtime."""
        self._add_task({
            "name": name,
            "cron": cron,
            "event": event_name,
            "data": data or {}
        })
    
    def remove_task(self, name: str) -> bool:
        """Remove a scheduled task."""
        try:
            self._scheduler.remove_job(name)
            return True
        except Exception:
            return False
    
    @property
    def scheduled_tasks(self) -> List[str]:
        """List all scheduled task names."""
        if not self._scheduler:
            return []
        return [job.id for job in self._scheduler.get_jobs()]
