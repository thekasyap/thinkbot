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
        # Hide API key from error messages
        error_msg = str(exc)
        if "key=" in error_msg:
            error_msg = error_msg.split("key=")[0] + "key=***HIDDEN***"
        return f"[Gemini request failed: {error_msg}]"



# ---------------------------------------------------------------------------
# Student profile storage
# ---------------------------------------------------------------------------


@dataclass
class LearningSession:
    question_id: int
    difficulty: str
    answer: str
    correct: bool
    response_time: float  # seconds
    answer_changes: int
    hints_used: int
    timestamp: str

@dataclass
class StudentProfile:
    name: str
    quizzes: int = 0
    correct: int = 0
    total_response_time: float = 0.0
    total_answer_changes: int = 0
    total_hints_used: int = 0
    learning_sessions: List[dict] = None
    learning_style: str = "unknown"  # visual, auditory, kinesthetic, reading
    preferred_difficulty: str = "medium"
    engagement_score: float = 0.0
    last_activity: str = ""
    
    def __post_init__(self):
        if self.learning_sessions is None:
            self.learning_sessions = []

    @property
    def accuracy(self) -> float:
        return self.correct / self.quizzes if self.quizzes else 0.0

    @property
    def average_response_time(self) -> float:
        return self.total_response_time / self.quizzes if self.quizzes else 0.0

    @property
    def hesitation_score(self) -> float:
        """Higher score = more hesitation (answer changes)"""
        return self.total_answer_changes / self.quizzes if self.quizzes else 0.0

    @property
    def engagement_level(self) -> str:
        """Determine engagement based on multiple factors"""
        if self.quizzes < 2:
            return "learning"
        
        # Calculate engagement score based on multiple factors
        accuracy_score = self.accuracy * 100
        time_score = max(0, 100 - (self.average_response_time / 2))  # Lower time = higher score
        consistency_score = max(0, 100 - (self.hesitation_score * 50))  # Lower hesitation = higher score
        hint_score = max(0, 100 - (self.total_hints_used / self.quizzes * 20))  # Lower hints = higher score
        
        # Weighted engagement score
        engagement_score = (accuracy_score * 0.4 + time_score * 0.2 + consistency_score * 0.2 + hint_score * 0.2)
        
        # Update the stored engagement score
        self.engagement_score = engagement_score
        
        # Determine engagement level based on score
        if engagement_score >= 80:
            return "highly_engaged"
        elif engagement_score >= 60:
            return "engaged"
        elif engagement_score >= 40:
            return "moderate"
        elif engagement_score >= 20:
            return "struggling"
        else:
            return "disengaged"

    @property
    def learning_pace(self) -> str:
        """Determine learning pace based on response time"""
        avg_time = self.average_response_time
        if avg_time < 20:
            return "fast"
        elif avg_time < 60:
            return "moderate"
        else:
            return "slow"

    @property
    def path(self) -> Path:
        return DATA_DIR / f"student_{self.name}.json"

    def save(self) -> None:
        DATA_DIR.mkdir(exist_ok=True)
        with self.path.open("w", encoding="utf-8") as fh:
            json.dump(asdict(self), fh, indent=2)

    @classmethod
    def load(cls, name: str) -> "StudentProfile":
        DATA_DIR.mkdir(exist_ok=True)
        path = DATA_DIR / f"student_{name}.json"
        if path.exists():
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            # Handle backward compatibility
            if "learning_sessions" not in data:
                data["learning_sessions"] = []
            if "learning_style" not in data:
                data["learning_style"] = "unknown"
            if "preferred_difficulty" not in data:
                data["preferred_difficulty"] = "medium"
            if "engagement_score" not in data:
                data["engagement_score"] = 0.0
            if "last_activity" not in data:
                data["last_activity"] = ""
            return cls(**data)
        return cls(name=name)

    def record_session(self, question_id: int, difficulty: str, answer: str, 
                      correct: bool, response_time: float, answer_changes: int = 0, 
                      hints_used: int = 0) -> None:
        """Record a complete learning session with detailed metrics"""
        from datetime import datetime
        
        session = LearningSession(
            question_id=question_id,
            difficulty=difficulty,
            answer=answer,
            correct=correct,
            response_time=response_time,
            answer_changes=answer_changes,
            hints_used=hints_used,
            timestamp=datetime.now().isoformat()
        )
        
        self.learning_sessions.append(asdict(session))
        self.quizzes += 1
        self.total_response_time += response_time
        self.total_answer_changes += answer_changes
        self.total_hints_used += hints_used
        
        if correct:
            self.correct += 1
            
        # Update learning style based on patterns
        self._update_learning_style()
        
        # Update engagement score
        self._update_engagement_score()
        
        self.last_activity = datetime.now().isoformat()
        self.save()

    def _update_learning_style(self) -> None:
        """Analyze patterns to determine learning style"""
        if len(self.learning_sessions) < 5:
            return
            
        # Simple heuristic: fast responders might be visual learners
        # Slow, careful responders might be reading learners
        avg_time = self.average_response_time
        accuracy = self.accuracy
        
        if avg_time < 30 and accuracy > 0.7:
            self.learning_style = "visual"
        elif avg_time > 60 and accuracy > 0.6:
            self.learning_style = "reading"
        elif self.total_hints_used > self.quizzes * 0.3:
            self.learning_style = "kinesthetic"
        else:
            self.learning_style = "auditory"

    def _update_engagement_score(self) -> None:
        """Calculate engagement score based on multiple factors"""
        if self.quizzes == 0:
            self.engagement_score = 0.0
            return
            
        # Factors: accuracy, response time, consistency
        accuracy_factor = self.accuracy
        time_factor = max(0, 1 - (self.average_response_time / 120))  # Normalize to 2 minutes
        consistency_factor = 1 - (self.hesitation_score / 3)  # Less hesitation = more consistent
        
        self.engagement_score = (accuracy_factor * 0.5 + time_factor * 0.3 + consistency_factor * 0.2)

    def get_learning_insights(self) -> dict:
        """Generate insights for teachers/educators"""
        return {
            "student_name": self.name,
            "total_quizzes": self.quizzes,
            "accuracy": round(self.accuracy * 100, 1),
            "learning_style": self.learning_style,
            "engagement_level": self.engagement_level,
            "learning_pace": self.learning_pace,
            "average_response_time": round(self.average_response_time, 1),
            "hesitation_score": round(self.hesitation_score, 2),
            "engagement_score": round(self.engagement_score, 2),
            "last_activity": self.last_activity,
            "needs_attention": self.engagement_level in ["struggling", "moderate"] and self.accuracy < 0.5
        }

    def record(self, correct: bool) -> None:
        """Legacy method for backward compatibility"""
        self.record_session(0, "unknown", "", correct, 0.0)


if __name__ == "__main__":  # pragma: no cover
    # small manual test when executed directly
    print(call_llm([{"role": "user", "content": "Hello"}]))
