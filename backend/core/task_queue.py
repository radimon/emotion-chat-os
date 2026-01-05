import asyncio
from dataclasses import dataclass

@dataclass
class ChatJob:
    job_id: str
    user_id: str
    message: str

class TaskQueue:
    """Async producer/consumer queue."""
    def __init__(self, maxsize: int = 200):
        self._q: asyncio.Queue[ChatJob] = asyncio.Queue(maxsize=maxsize)

    async def put(self, job: ChatJob) -> None:
        await self._q.put(job)
    
    async def get(self) -> ChatJob:
        return await self._q.get()
    
    def task_done(self) -> None:
        self._q.task_done()
    
    def qsize(self) -> int:
        return self._q.qsize()