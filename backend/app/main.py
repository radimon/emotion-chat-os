from fastapi import FastAPI
from pydantic import BaseModel

from backend.services.emotion import EmotionAnalyzer
from backend.services.policy import PolicyEngine

app = FastAPI(title="Emotion Chat MVP")

emotion = EmotionAnalyzer()
policy = PolicyEngine()

class ChatRequest(BaseModel):
    user_id: str
    message: str

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/chat")
def chat(req: ChatRequest):
    emo = emotion.analyze(req.message)
    pol = policy.decide(emo)

    if pol.style == "supportive":
        reply = ""
    elif pol.style == "deescalate":
        reply = ""
    elif pol.style == "clarify":
        reply = ""
    else:
        reply = ""

    return {
        "reply": reply,
        "emotion": emo.__dict__,
        "policy": pol.__dict__,
    }