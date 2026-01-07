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
    Background worker & streaming orchestrator

    職責分工：
    - run_forever():
        * 維持 queue 消費（未來可加 retry / rate limit / persistence）
        * 不直接呼叫 LLM（避免跟 WS 重複）
    - stream_reply():
        * 唯一的 LLM 呼叫入口
        * 負責：
            - session memory
            - emotion / policy
            - streaming chunks
            - 最終結果回存
    """

    def __init__(self, queue: TaskQueue, result_ttl_sec: int = 300):
        self.queue = queue

        # --- core services ---
        self.emotion = EmotionAnalyzer()
        self.policy = PolicyEngine()
        self.llm = OpenAILLMClient()
        self.sessions = SessionStore(max_turns=20)

        # --- in-memory result store ---
        self.results: Dict[str, ChatResult] = {}
        self._events: Dict[str, asyncio.Event] = {}

        self.result_ttl_sec = result_ttl_sec

    # ============ housekeeping ============
    def _cleanup_expired(self) -> None:
        now = time.time()
        expired = [
            k for k, v in self.results.items()
            if now - v.created_at > self.result_ttl_sec
        ]
        for k in expired:
            self.results.pop(k, None)

    # ============ background worker (queue) ============
    async def run_forever(self) -> None:
        """
        Background consumer.

        目前版本：
        - 僅負責把 job 從 queue 拿掉
        - 不直接處理 LLM（避免與 WebSocket streaming 重複）
        """
        while True:
            job = await self.queue.get()
            try:
                # 預留：未來可做 retry / rate limit / persistence
                await asyncio.sleep(0)
            finally:
                self.queue.task_done()

    # ============ polling / SSE support ============
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

    # ============ WebSocket streaming ============
    async def stream_reply(self, job: ChatJob, session_id: str):
        """
        Streaming reply generator (WebSocket 專用)

        流程：
        1. 記錄 user message 到 session
        2. 分析 emotion / policy
        3. 組 messages（含 system prompt + history）
        4. streaming LLM output
        5. 回存 assistant message + ChatResult
        """

        user_id = job.user_id

        # ---- session: user message ----
        self.sessions.add_user_message(
            user_id=user_id,
            session_id=session_id,
            content=job.message
        )


        # ---- emotion & policy ----
        emo = self.emotion.analyze(job.message)
        pol = self.policy.decide(emo)


        # ---- conversation history ----
        history = self.sessions.get_history(user_id, session_id)

        messages = [
            {"role": "system", "content": pol.system_prompt},
            *history
        ]

        full_reply = ""


        # ---- streaming from LLM ----
        async for chunk in self.llm.stream_chat_messages(
            messages=messages,
            max_words=pol.max_words,
        ):
            full_reply += chunk
            yield chunk


        # ---- session: assistant message ----
        self.sessions.add_assistant_message(
            user_id=user_id,
            session_id=session_id,
            content=full_reply
        )


        # ---- store final result (for polling / SSE) ----
        self.results[job.job_id] = ChatResult(
            job_id=job.job_id,
            reply=full_reply,
            emotion=emo.__dict__,
            policy=pol.__dict__,
            created_at=time.time(),
        )


        # ---- notify SSE waiters ----
        evt = self._events.get(job.job_id)
        if evt:
            evt.set()

        self._cleanup_expired()
