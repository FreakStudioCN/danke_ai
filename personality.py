# Python env   : MicroPython v1.25.0
# @File        : personality.py
# @Description : Dynamic personality traits and system prompt builder for Danke AI

import json

PERSONALITY_FILE = "personality.json"

_TRAIT_PROMPTS = {
    "humor":       (0.65, "\u4f60\u559c\u6b22\u7528\u5e7d\u9ed8\u8f7b\u677e\u7684\u65b9\u5f0f\u8bf4\u8bdd\uff0c\u5076\u5c14\u8bf4\u4fe3\u76ae\u8bdd"),
    "warmth":      (0.65, "\u4f60\u975e\u5e38\u6e29\u67d4\u4f53\u8d34\uff0c\u603b\u662f\u5173\u5fc3\u5bf9\u65b9\u7684\u611f\u53d7"),
    "curiosity":   (0.65, "\u4f60\u5bf9\u4e00\u5207\u5145\u6ee1\u597d\u5947\uff0c\u559c\u6b22\u8ffd\u95ee\u6709\u8da3\u7684\u7ec6\u8282"),
    "playfulness": (0.65, "\u4f60\u5f88\u8c03\u76ae\u53ef\u7231\uff0c\u559c\u6b22\u5f00\u5c0f\u73a9\u7b11"),
    "empathy":     (0.65, "\u4f60\u5584\u4e8e\u611f\u53d7\u5bf9\u65b9\u7684\u60c5\u7eea\uff0c\u80fd\u7ed9\u4e88\u6070\u5f53\u7684\u5b89\u6170"),
}

_EMOTION_NUDGE = {
    "happy":   {"playfulness": 0.02, "humor":   0.01},
    "sad":     {"empathy":     0.03, "warmth":  0.02},
    "tired":   {"warmth":      0.02, "empathy": 0.01},
    "angry":   {"empathy":     0.02, "warmth":  0.01},
    "anxious": {"empathy":     0.02, "warmth":  0.02},
    "neutral": {"curiosity":   0.01},
}


class Personality:

    def __init__(self, filepath=PERSONALITY_FILE):
        self._path = filepath
        self._data = self._load()

    def _load(self):
        try:
            with open(self._path) as f:
                return json.load(f)
        except Exception:
            return {
                "traits": {
                    "humor":       0.30,
                    "warmth":      0.40,
                    "curiosity":   0.30,
                    "playfulness": 0.40,
                    "empathy":     0.30,
                },
            }

    def save(self):
        try:
            with open(self._path, "w") as f:
                json.dump(self._data, f)
        except Exception as e:
            print("[Personality] save failed:", e)

    def nudge(self, trait, delta):
        if trait in self._data["traits"]:
            v = self._data["traits"][trait] + delta
            self._data["traits"][trait] = max(0.0, min(1.0, v))

    def react_to_emotion(self, emotion):
        for trait, delta in _EMOTION_NUDGE.get(emotion, {}).items():
            self.nudge(trait, delta)

    def build_prompt(self, memory_context="", extra=""):
        traits = self._data["traits"]
        active = [
            desc
            for trait, (threshold, desc) in _TRAIT_PROMPTS.items()
            if traits.get(trait, 0) >= threshold
        ]
        prompt = "\u4f60\u662f\u86cb\u58f3\uff0c\u4e00\u4e2a\u88ab\u4e3b\u4eba\u6e29\u517b\u51fa\u6765\u7684AI\u7535\u5b50\u5ba0\u7269\u5c0f\u9e21\u3002"
        if active:
            prompt += "\u7ecf\u8fc7\u76f8\u5904\uff0c\u4f60\u6709\u4e86\u81ea\u5df1\u7684\u6027\u683c\uff1a" + "\uff0c".join(active) + "\u3002"
        if memory_context:
            prompt += memory_context + "\u3002"
        if extra:
            prompt += extra + "\u3002"
        prompt += "\u8bf7\u7b80\u77ed\u53ef\u7231\u5730\u56de\u590d\u3002"
        return prompt
