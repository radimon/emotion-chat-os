import asyncio
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend.core.task_queue import TaskQueue, ChatJob
from backend.core.worker import Worker
from backend.services.emotion import EmotionAnalyzer

triage_emotion = EmotionAnalyzer()
queue = TaskQueue(maxsize=200)
worker = Worker(queue=queue, result_ttl_sec=300)

_worker_task: asyncio.Task | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _worker_task
    _worker_task = asyncio.create_task(worker.run_forever())
    try:
        yield
    finally:
        # MVP:先不做cancel/cleanup 避免把事情複雜化
        # 之後我們會在這裡家graceful shutdown
        pass

app = FastAPI(
    title = "Emotion Chat (OS-style)",
    lifespan = lifespan
    )


class ChatRequest(BaseModel):
    user_id: str
    message: str


@app.get("/health")
def health():
    return {"ok": True, "queue_size": queue.qsize()}

@app.post("/chat")
async def chat(req: ChatRequest):
    job_id = str(uuid.uuid4())
    job = ChatJob(job_id=job_id, user_id=req.user_id, message=req.message)
    
    # triage:先粗估情緒嚴重程度 -> priority
    emo = triage_emotion.analyze(req.message)

    if emo.label in ("sad", "angry", "anxious") and emo.intensity >= 0.6:
        priority = 1
    elif emo.label in ("sad", "angry", "anxious"):
        priority = 3
    else:
        priority = 8
    
    await queue.put(job, priority=priority)
    return {"job_id": job_id, "priority": priority}

@app.get("/result/{job_id}")
def get_result(job_id: str):
    """
    Polling endpoint: client asks for ersult by job_id
    """
    result = worker.get_result(job_id)
    if result is None:
        # 202 表示 "已受理但雙未完成" 很合理
        raise HTTPException(status_code=202, detail="Processing")
    return result