import asyncio
from typing import AsyncGenerator

class LLMClient:
    async def stream_chat(self, prompt: str) -> AsyncGenerator[str, None]:
        """
        Abstract streaming interface.
        Yield partial text chunks.
        """
        raise NotImplementedError
    

class MockLLMClient(LLMClient):
    async def stream_chat(self, prompt: str):
        text = f"我理解你正在經歷的狀態。你剛剛提到：{prompt}"
        for word in text.split(" "):
            await asyncio.sleep(0.3)
            print("LLM: yield", word)
            yield word + " "
        print("LLM: done")