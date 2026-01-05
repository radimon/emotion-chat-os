import asyncio
import time
from dataclasses import dataclass
from typing import Dict, Optional

from backend.core.task_queue import TaskQueue, ChatJob
from backend.services.emotion import EmotionAnalyzer
from backend.services.policy import PolicyEngine

@dataclass
class ChatResult:
    job_id: str
    reply: str
    emotion: dict
    policy: dict
    created_at: float

class Worker:
    """
    Background worker:
    - consumes ChatJob from queue
    - produces ChatResult into in-memory store
    """

    def __init__(self, queue: TaskQueue,  result_ttl_sec: int = 300):
        self.queue = queue
        self.emotion = EmotionAnalyzer()
        self.policy = PolicyEngine()
        self.results: Dict[str, ChatResult] = {}
        self.result_ttl_sec = result_ttl_sec

    def _compose_reply(self, style: str) -> str:
        if style == "supportive":
            return "我聽到你現在難受。我在這裡陪你。你願意多說一點發生了什麼嗎？"
        if style == "deescalate":
            return "我感覺你很不舒服。我們先把事情釐清：是什麼點讓你最生氣或最委屈？"
        if style == "clarify":
            return "我聽到你很金崩。我可以先陪你把情擴拆開：你最擔心的是哪個部分？"
        return "收到。我可以更了解一下你的情況嗎？"
    
    def _cleanup_expired(self) -> None:
        now = time.time()
        expired = [k for k, v in self.results.items() if now - v.created_at > self.result_ttl_sec]
        for k in expired:
            self.results.pop(k, None)
        
    async def run_forever(self) -> None:
        while True:
            job = await self.queue.get()
            try:
                # --- Timeout: 模擬/預防模型卡住 ---
                # 先把 處理job 包成一個coroutine, 再用 wait_for 限時
                async def handle_one():
                    emo = self.emotion.analyze(job.message)
                    pol = self.policy.decide(emo)
                    reply = self._compose_reply(pol.style)
                
                    self.results[job.job_id] = ChatResult(
                        job_id = job.job_id,
                        reply = reply,
                        emotion = emo.__dict__,
                        policy = pol.__dict__,
                        created_at = time.time(),
                    )
            
                try:
                   await asyncio.wait_for(handle_one(), timeout=2.0)
                except asyncio.TimeoutError:
                    # fallback: 超時救回 安全的短回覆
                    self.results[job.job_id] = ChatResult(
                        job = job.job_id,
                        reply = "我收到你的訊息了，我正在整理要怎麼回比較好，能再多給我一點背景嗎？",
                        emotion = {"label": "unknown", "intensity": 0.0, "confidence": 0.0},
                        policy = {"style": "fallback", "max_words": 60},
                        created_at = time.time(),
                    )
                self._cleanup_expired()
        
            finally:
                self.queue.task_done()
    
    def get_result(self, job_id: str) -> Optional[dict]:
        r = self.results.get(job_id)
        if not r:
            return None
        return {
            "job_id": r.job_id,
            "reply": r.reply,
            "emotion": r.emotion,
            "policy": r.policy,
        }
        