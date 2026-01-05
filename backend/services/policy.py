from dataclasses import dataclass
from backend.services.emotion import EmotionState

@dataclass
class PolicyDecision:
    style: str       # "supportive" | "deescalte" | "clarify" | "neutral"
    max_words: int

class PolicyEngine:
    """
    MVP: map emotion -> response policy
    Later: add risk tiers, uncertainty handling, and safety routing.
    """
    def decide(self, emo: EmotionState) -> PolicyDecision:
        if emo.label == "sad" and emo.intensity >= 0.5:
            return PolicyDecision(style="supportive", max_words=90)
        if emo.label == "angry" and emo.intensity >= 0.5:
            return PolicyDecision(style="deescalte", max_words=90)
        if emo.label == "anxious" and emo.intensity >= 0.5:
            return PolicyDecision(style="clarify", max_words=90)
        
        return PolicyDecision(style="neutral", max_words=70)