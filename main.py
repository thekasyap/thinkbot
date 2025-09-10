"""Core utilities for the ThinkBot demo.

Provides a minimal Gemini client and a small JSON-based ``StudentProfile`` to
keep resource usage low for free-tier hosting such as Vercel's hobby plan.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List

import requests

# Directory where student progress JSON files are stored
DATA_DIR = Path("data")

# Gemini configuration
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def call_llm(messages: List[dict]) -> str:
    """Call Gemini via its REST API and return the text response.

    ``messages`` uses the familiar ``{"role": ..., "content": ...}`` format.
    To conserve free-tier quotas we disable the "thinking" feature by setting
    the ``thinkingBudget`` to zero.
    """

    if not GEMINI_API_KEY:
        return "[Gemini API key not set]"

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent"
    )
    payload = {
        "contents": [
            {"role": m["role"], "parts": [{"text": m["content"]}]} for m in messages
        ],
        "generationConfig": {"thinkingConfig": {"thinkingBudget": 0}},
    }
    params = {"key": GEMINI_API_KEY}
    try:
        r = requests.post(url, params=params, json=payload, timeout=15)
        r.raise_for_status()
        data = r.json()
        return (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )
    except Exception as exc:  # pragma: no cover - network errors
        return f"[Gemini request failed: {exc}]"


# ---------------------------------------------------------------------------
# Student profile storage
# ---------------------------------------------------------------------------


@dataclass
class StudentProfile:
    name: str
    quizzes: int = 0
    correct: int = 0

    @property
    def accuracy(self) -> float:
        return self.correct / self.quizzes if self.quizzes else 0.0

    @property
    def path(self) -> Path:
        return DATA_DIR / f"student_{self.name}.json"

    def save(self) -> None:
        DATA_DIR.mkdir(exist_ok=True)
        with self.path.open("w", encoding="utf-8") as fh:
            json.dump(asdict(self), fh)

    @classmethod
    def load(cls, name: str) -> "StudentProfile":
        DATA_DIR.mkdir(exist_ok=True)
        path = DATA_DIR / f"student_{name}.json"
        if path.exists():
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            return cls(**data)
        return cls(name=name)

    def record(self, correct: bool) -> None:
        self.quizzes += 1
        if correct:
            self.correct += 1
        self.save()


if __name__ == "__main__":  # pragma: no cover
    # small manual test when executed directly
    print(call_llm([{"role": "user", "content": "Hello"}]))
