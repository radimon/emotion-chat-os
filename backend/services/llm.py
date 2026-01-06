import asyncio
import os
from typing import AsyncGenerator
from openai import AsyncOpenAI
from dotenv import load_dotenv

# ========== load env ==========
load_dotenv()

# ========== Abstract Interface ==========
class LLMClient:
    async def stream_chat(self, prompt: str) -> AsyncGenerator[str, None]:
        """
        Abstract streaming interface.
        Yield partial text chunks.
        """
        raise NotImplementedError

# ========== OpenAI Implementation ==========
class OpenAILLMClient(LLMClient):
    """
    OpenAI Streaming LLM Client
    """
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        
        # init OpenAI async client
        self.client = AsyncOpenAI(api_key=api_key)

        # Debug / verification log
        print("LLM: OpenAI client initialized")
        print("LLM: API key loaded =", True)
    
    async def stream_chat(self, prompt: str) -> AsyncGenerator[str, None]:
        """
        Yield partial tokens from OpenAI streaming API
        """
        print("LLM: sending request to OpenAI")

        try: 
            stream = await self.client.chat.completions.create(
                model = "gpt-4o-mini",
                messages = [
                    {
                        "role": "system",
                        "content": "你是一位溫和、支持性的助理，專注於情緒理解與回應。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                stream = True,
            )

            first_chunk = True
            async for chunk in stream:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    if first_chunk:
                        print("LLM: received first chunk from OpenAI")
                        first_chunk = False
                    yield delta.content
            
            print("LLM: stream finished")
        
        except Exception as e:
            print("LLM: streaming error", repr(e))
            yield " (抱歉，我現在有點卡住，但我有收到你的訊息。)"


# ========== Mock Implementation (for testing / fallback) ==========
class MockLLMClient(LLMClient):
    async def stream_chat(self, prompt: str):
        text = f"我理解你正在經歷的狀態。你剛剛提到：{prompt}"
        for word in text.split(" "):
            await asyncio.sleep(0.3)
            print("LLM(Mock): yield", word)
            yield word + " "
        print("LLM(Mock): done")  