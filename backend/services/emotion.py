from dataclasses import dataclass

@dataclass
class EmotionState:
    label: str         # "sad" | "angry" | "anxious" | "happy" | "neutral"
    intensity: float   # 0.0 ~ 1.0
    confidence: float  # 0.0 ~ 1.0


class EmotionAnalyzer:
    """
    MVP: rule-based emotion detector.
    Later: replace with ML/LLM; keep the same output contract.
    """
    def analyze(self, text: str) -> EmotionState:
        t = (text or "").lower().strip()

        if not t:
            return EmotionState(label="neutral", intensity=0.10, confidence=0.40)
    
        sad_keys = ["難過", "傷心", "想哭", "sad", "depressed", "cry", "hopeless"]
        angry_keys = ["生氣", "火大", "憤怒", "angry", "mad", "furious"]
        anxious_keys = ["焦慮", "緊張", "怕", "不安", "anxious", "panic", "worried"]
        happy_keys = ["開心", "快樂", "幸福", "happy", "exicted", "great"]

        if any(k in t for k in sad_keys):
            return EmotionState(label="sad", intensity=0.75, confidence=0.60)
        if any(k in t for k in angry_keys):
            return EmotionState(label="angry", intensity=0.70, confidence=0.60)
        if any(k in t for k in anxious_keys):
            return EmotionState(label="anxious", intensity=0.65, confidence=0.55)
        if any(k in t for k in happy_keys):
            return EmotionState(label="happy", intensity=0.55, confidence=0.55)
        
        return EmotionState(label="neutral", intensity=0.25, confidence=0.50)
        