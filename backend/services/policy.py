from dataclasses import dataclass
from backend.services.emotion import EmotionResult

@dataclass
class ReplyPolicy:
    style: str       # "supportive" | "deescalte" | "clarify" | "neutral"
    max_words: int
    system_prompt: str

class PolicyEngine:
    """
    Decide reply policy based on emotion analysis
    """
    def decide(self, emotion):
        label = emotion.label
        intensity = emotion.intensity

        # 高情緒強度：優先安撫 / 降溫
        if label in ("sad", "anxious") and intensity >= 0.6:
            return ReplyPolicy(
                style = "supportive",
                max_words = 80,
                system_prompt = (
                    "你是一位溫和、富有圖領新的對話者。"
                    "請先接至對方的情緒，避免給建議或說教，"
                    "多使用理解與陪伴的語氣。"
                )
            )
        
        if label == "angry" and intensity >= 0.6:
            return ReplyPolicy(
                style = "deescalate",
                max_words = 60,
                system_prompt = (
                    "你是一位冷靜、穩定的對話者。"
                    "請幫助對方降溫，避免火上加油，"
                    "引導對方釐清事情而非指責他人。"
                )
            )
        
        # 低強度或中性
        return ReplyPolicy(
            style = "neutral",
            max_words = 100,
            system_prompt = (
                "你是一位理性、清楚的助理，"
                "請根據使用者的訊息提供回應。"
            )
        )