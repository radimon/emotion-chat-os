import asyncio
import time
from dataclasses import dataclass, field

@dataclass(order=True)
class PriorityizedItem:
    priority: int
    created_at: float = field(compare=False)
    job: "ChatJob" = field(compare=False)

@dataclass
class ChatJob:
    job_id: str
    user_id: str
    message: str

class TaskQueue:
    """Async producer/consumer queue."""
    def __init__(self, maxsize: int = 200):
        self._q: asyncio.PriorityQueue[PriorityizedItem] = asyncio.PriorityQueue(maxsize=maxsize)

    async def put(self, job: ChatJob, priority: int = 10) -> None:
        item = PriorityizedItem(priority=priority, created_at=time.time(), job=job)
        await self._q.put(job)
    
    async def get(self) -> ChatJob:
        item = await self._q.get()
        return item.job
    
    def task_done(self) -> None:
        self._q.task_done()
    
    def qsize(self) -> int:
        return self._q.qsize()