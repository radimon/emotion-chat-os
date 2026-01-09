from dataclasses import dataclass
from typing import Dict

@dataclass
class PolicyResult:
    style: str
    priority: int
    max_words: str
    system_prompt: str
    prompt_context: str
    rationale: Dict[str, float]

class PolicyEngine:
    def decide(self, emotion) -> PolicyResult:
        fuzzy = emotion.fuzzy

        sadness = fuzzy.get("sadness", 0.0)
        anxiety = fuzzy.get("anxiety", 0.0)
        anger = fuzzy.get("anger", 0.0)
        calm = fuzzy.get("calm", 0.0)

        # ----- Priority (1 = highest) -----
        urgency_score = max(
            sadness * 0.9,
            anxiety * 1.0,
            anger * 0.7,
        )
        
        if urgency_score >= 0.7:
            priority = 1
        elif urgency_score >= 0.4:
            priority = 3
        else:
            priority = 8

        # ----- Style -----
        style_scores = {
            "supportive": sadness,
            "reassure": anxiety,
            "deescalate": anger,
            "neutral": calm,
        }

        style = max(style_scores, key=style_scores.get)

        SYSTEM_PROMPTS = {
            "supportive": "你是一位溫柔、具有高度同理心的助理，請先安撫情緒，不要急著建議。",
            "reassure": "你是一位冷靜且可靠的助理，請幫助對方降低焦慮並釐清狀況",
            "deescalate": "你是一位中立、降溫型助理，請避免刺激性語言，協助情緒緩和。",
            "neutral": "你是一位理性且簡潔的助理。"
        }

        # ----- max words (resource control) -----
        if urgency_score >= 0.7:
            max_words = 40
        elif urgency_score >= 0.4:
            max_words = 60
        else:
            max_words = 80

        prompt_context = (
            f"情緒分析結果："
            f"悲傷 {sadness:.2f}, "
            f"焦慮 {anxiety:.2f}, "
            f"憤怒 {anger:.2f}, "
            f"平靜 {calm:.2f}。"
            "請依據這些情緒強度調整回應語氣與策略。"
        )

        return PolicyResult(
            style = style,
            priority = priority,
            max_words = max_words,
            system_prompt = SYSTEM_PROMPTS[style],
            prompt_context = prompt_context,
            rationale = {
                "urgency_score": urgency_score,
                **style_scores,
            }
        )