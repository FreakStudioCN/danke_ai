# Python env   : MicroPython v1.25.0
# @File        : memory.py
# @Description : Persistent episodic memory and relationship tracking for Danke AI

import json
import time

MAX_EPISODES = 15
MEMORY_FILE  = "memory.json"

# Closeness thresholds: score = total_rounds + touch_count // 5
_CLOSENESS_STEPS = [0, 1, 3, 7, 15, 30, 60, 100, 150, 250, 500]

def _calc_closeness(score):
    for i, t in enumerate(_CLOSENESS_STEPS):
        if score < t:
            return i - 1
    return 10


class MemoryStore:

    def __init__(self, filepath=MEMORY_FILE):
        self._path = filepath
        self._data = self._load()

    def _load(self):
        try:
            with open(self._path) as f:
                return json.load(f)
        except Exception:
            return {
                "episodes": [],
                "relationship": {
                    "total_rounds": 0,
                    "touch_count":  0,
                    "closeness":    0,
                },
            }

    def save(self):
        try:
            with open(self._path, "w") as f:
                json.dump(self._data, f)
        except Exception as e:
            print("[Memory] save failed:", e)

    def add_episode(self, user_text, emotion="neutral"):
        summary = user_text[:60].strip()
        self._data["episodes"].append({"ts": time.time(), "summary": summary, "emotion": emotion})
        if len(self._data["episodes"]) > MAX_EPISODES:
            self._data["episodes"] = self._data["episodes"][-MAX_EPISODES:]
        rel = self._data["relationship"]
        rel["total_rounds"] += 1
        rel["closeness"] = _calc_closeness(rel["total_rounds"] + rel["touch_count"] // 5)

    def add_touch(self):
        rel = self._data["relationship"]
        rel["touch_count"] += 1
        rel["closeness"] = _calc_closeness(rel["total_rounds"] + rel["touch_count"] // 5)

    def build_context(self):
        rel      = self._data["relationship"]
        episodes = self._data["episodes"]
        rounds   = rel["total_rounds"]
        if rounds == 0:
            return ""
        parts = []
        if rounds < 5:
            parts.append("\u6211\u4eec\u5df2\u7ecf\u804a\u8fc7{}\u6b21\u4e86".format(rounds))
        else:
            parts.append("\u6211\u4eec\u662f\u8001\u670b\u53cb\u4e86\uff0c\u5df2\u7ecf\u804a\u4e86{}\u6b21".format(rounds))
        if episodes:
            recent = episodes[-3:]
            parts.append("\u6211\u8bb0\u5f97\uff1a" + "\uff1b".join(e["summary"] for e in recent))
        return "\uff0c".join(parts)

    def greeting(self):
        rounds   = self._data["relationship"]["total_rounds"]
        episodes = self._data["episodes"]
        if rounds == 0:
            return "\u4f60\u597d\uff0c\u6211\u662f\u86cb\u58f3\uff0c\u6709\u4ec0\u4e48\u53ef\u4ee5\u5e2e\u4f60\u7684\uff1f"
        if rounds < 3:
            base = "\u4f60\u6765\u554a\uff01\u86cb\u58f3\u4e00\u76f4\u5728\u7b49\u4f60\u5462\uff5e"
        elif rounds < 10:
            base = "\u4e3b\u4eba\u4f60\u6765\u4e86\uff01\u86cb\u58f3\u597d\u60f3\u4f60\u54e6\uff5e"
        else:
            base = "\u4e3b\u4eba\u4e3b\u4eba\uff01\u7ec8\u4e8e\u7b49\u5230\u4f60\u554a\uff01\u86cb\u58f3\u53ef\u60f3\u4f60\u4e86\uff01"
        if episodes:
            recall = episodes[-1]["summary"][:20]
            base += "\u4e0a\u6b21\u4f60\u8bf4\u7684\u300c" + recall + "\u300d\uff0c\u86cb\u58f3\u4e00\u76f4\u8bb0\u7740\u5462\uff5e"
        return base

    @property
    def total_rounds(self):
        return self._data["relationship"]["total_rounds"]

    @property
    def closeness(self):
        return self._data["relationship"]["closeness"]
