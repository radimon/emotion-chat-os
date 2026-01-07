import asyncio
import time
from dataclasses import dataclass
from typing import Dict, Optional

from backend.core.task_queue import TaskQueue, ChatJob
from backend.services.emotion import EmotionAnalyzer
from backend.services.policy import PolicyEngine
from backend.services.llm import OpenAILLMClient
from backend.core.session_store import SessionStore

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
        self.llm = OpenAILLMClient()
        self.results: Dict[str, ChatResult] = {}
        self._events: Dict[str, asyncio.Event] = {}
        self.result_ttl_sec = result_ttl_sec
        self.sessions = SessionStore(max_turns=20)
    
    def _cleanup_expired(self) -> None:
        now = time.time()
        expired = [
            k for k, v in self.results.items()
            if now - v.created_at > self.result_ttl_sec
        ]
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
                    
                    chunks = []
                    async for chunk in self.llm.stream_chat(job.message):
                        chunks.append(chunk)
                    
                    reply = "".join(chunks)

                    self.results[job.job_id] = ChatResult(
                        job_id = job.job_id,
                        reply = reply,
                        emotion = emo.__dict__,
                        policy = pol.__dict__,
                        created_at = time.time(),
                    )

                    evt = self._events.get(job.job_id)
                    if evt:
                        evt.set()
            
                try:
                   await asyncio.wait_for(handle_one(), timeout=2.0)
                except asyncio.TimeoutError:
                    # fallback: 超時救回 安全的短回覆
                    self.results[job.job_id] = ChatResult(
                        job_id = job.job_id,
                        reply = "我正在整理回應，能再多說一點你的狀況嗎？",
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
    
    def register_event(self, job_id: str) -> asyncio.Event:
        evt = asyncio.Event()
        self._events[job_id] = evt
        return evt
    
    def clear_event(self, job_id: str) -> None:
        self._events.pop(job_id, None)

    async def stream_reply(self, job, session_id: str):
        user_id = job.user_id

        # 紀錄使用者訊息
        self.sessoins.add_user_message(
            user_id = user_id,
            session_id = session_id,
            content = job.message
        )

        # 情緒與策略
        emo = self.emotion.analyze(job.message)
        pol = self.policy.decide(emo)

        # 取歷史對話
        history = self.sessoins.get_history(user_id, session_id)

        # 組 messages
        messages = [
            {"role": "system", "content": pol.system_prompt},
            *history
        ]

        full_reply = ""

        async for chunk in self.llm.stream_chat_messages(
            messages = messages,
            max_words = pol.max_words,
        ):
            full_reply += chunk
            yield chunk
        
        # 回存 assistant 回覆
        self.sessions.add_assistant_message(
            user_id = user_id,
            session_id = session_id,
            content = full_reply
        )