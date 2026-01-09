from dataclasses import dataclass
from typing import Dict

@dataclass
class EmotionResult:
    label: str         
    intensity: float   
    confidence: float
    fuzzy: Dict[str, float]


class EmotionAnalyzer:
    def analyze(self, text: str) -> EmotionResult:
        text = text.lower()

        sadness = 0.0
        anger = 0.0
        anxiety = 0.0

        # very naive lexical cues (可解釋)
        if any(w in text for w in ["累", "難過", "好煩", "撐不下去"]):
            sadness += 0.6
        
        if any(w in text for w in ["氣", "不爽", "受不了"]):
            anger += 0.6

        if any(w in text for w in ["怕", "擔心", "不知道怎麼辦"]):
            anxiety += 0.6
        
        # normalize / clamp
        sadness = min(sadness, 1.0)
        anger = min(anger, 1.0)
        anxiety = min(anxiety, 1.0)

        calm = max(0.0, 1.0 - max(sadness, anger, anxiety))

        fuzzy = {
            "sadness": sadness,
            "anger": anger,
            "anxiety": anxiety,
            "calm": calm,
        }

        # dominant label (for old system)
        label = max(fuzzy, key=fuzzy.get)
        intensity = fuzzy[label]

        return EmotionResult(
            label = label,
            intensity = intensity,
            confidence = 0.8,
            fuzzy = fuzzy,
        )