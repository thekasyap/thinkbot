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
    total_skipped: int = 0
    learning_sessions: List[dict] = None
    learning_style: str = "unknown"  # visual, auditory, kinesthetic, reading
    preferred_difficulty: str = "medium"
    engagement_score: float = 0.0
    last_activity: str = ""
    streak_days: int = 0  # consecutive days of activity
    improvement_trend: float = 0.0  # recent performance vs historical
    session_frequency: float = 0.0  # sessions per day
    difficulty_progression: List[str] = None  # track difficulty changes
    topic_preferences: dict = None  # track which topics student engages with most
    
    def __post_init__(self):
        if self.learning_sessions is None:
            self.learning_sessions = []
        if self.difficulty_progression is None:
            self.difficulty_progression = []
        if self.topic_preferences is None:
            self.topic_preferences = {}

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
    def skip_rate(self) -> float:
        """Percentage of questions skipped"""
        return self.total_skipped / self.quizzes if self.quizzes else 0.0

    @property
    def hint_dependency(self) -> float:
        """How often student uses hints (0-1 scale)"""
        return self.total_hints_used / self.quizzes if self.quizzes else 0.0

    @property
    def recent_performance(self) -> float:
        """Performance in last 10 questions"""
        if len(self.learning_sessions) < 2:
            return self.accuracy
        
        recent_sessions = self.learning_sessions[-10:] if len(self.learning_sessions) >= 10 else self.learning_sessions
        recent_correct = sum(1 for session in recent_sessions if session.get('correct', False))
        return recent_correct / len(recent_sessions) if recent_sessions else 0.0

    @property
    def consistency_score(self) -> float:
        """How consistent the student's performance is (lower variance = higher score)"""
        if len(self.learning_sessions) < 3:
            return 50.0  # neutral score for insufficient data
        
        # Calculate variance in accuracy over recent sessions
        recent_sessions = self.learning_sessions[-10:] if len(self.learning_sessions) >= 10 else self.learning_sessions
        accuracies = [1.0 if session.get('correct', False) else 0.0 for session in recent_sessions]
        
        if not accuracies:
            return 50.0
            
        mean_acc = sum(accuracies) / len(accuracies)
        variance = sum((acc - mean_acc) ** 2 for acc in accuracies) / len(accuracies)
        
        # Convert variance to consistency score (0-100, higher is more consistent)
        consistency = max(0, 100 - (variance * 100))
        return consistency

    @property
    def learning_momentum(self) -> float:
        """Positive momentum if improving, negative if declining"""
        if len(self.learning_sessions) < 5:
            return 0.0
            
        # Compare recent performance vs earlier performance
        recent_sessions = self.learning_sessions[-5:]
        earlier_sessions = self.learning_sessions[-10:-5] if len(self.learning_sessions) >= 10 else self.learning_sessions[:-5]
        
        if not earlier_sessions:
            return 0.0
            
        recent_perf = sum(1 for s in recent_sessions if s.get('correct', False)) / len(recent_sessions)
        earlier_perf = sum(1 for s in earlier_sessions if s.get('correct', False)) / len(earlier_sessions)
        
        return (recent_perf - earlier_perf) * 100  # -100 to +100 scale

    @property
    def engagement_level(self) -> str:
        """Enhanced engagement tracking with multiple sophisticated metrics"""
        if self.quizzes < 2:
            return "learning"
        
        # Core performance metrics (40% weight)
        accuracy_score = self.accuracy * 100
        recent_performance_score = self.recent_performance * 100
        
        # Behavioral engagement metrics (25% weight)
        skip_penalty = self.skip_rate * 50  # High skip rate reduces engagement
        hint_penalty = self.hint_dependency * 30  # Over-reliance on hints reduces engagement
        hesitation_penalty = min(self.hesitation_score * 25, 30)  # Excessive hesitation reduces engagement
        
        behavioral_score = max(0, 100 - skip_penalty - hint_penalty - hesitation_penalty)
        
        # Consistency and momentum metrics (20% weight)
        consistency_score = self.consistency_score
        momentum_bonus = max(0, min(self.learning_momentum, 20))  # Cap momentum bonus at 20 points
        momentum_score = 50 + momentum_bonus  # Base 50 + momentum bonus
        
        # Time efficiency metrics (15% weight)
        # Optimal response time is 15-45 seconds (not too fast, not too slow)
        avg_time = self.average_response_time
        if avg_time < 15:
            time_score = 60 + (avg_time / 15) * 20  # 60-80 for very fast
        elif avg_time <= 45:
            time_score = 80 + (45 - avg_time) / 30 * 20  # 80-100 for optimal range
        elif avg_time <= 90:
            time_score = 80 - (avg_time - 45) / 45 * 30  # 50-80 for slow
        else:
            time_score = max(20, 50 - (avg_time - 90) / 30 * 10)  # 20-50 for very slow
        
        # Calculate weighted engagement score
        engagement_score = (
            (accuracy_score * 0.25 + recent_performance_score * 0.15) +  # Core performance (40%)
            behavioral_score * 0.25 +  # Behavioral engagement (25%)
            (consistency_score * 0.15 + momentum_score * 0.05) +  # Consistency & momentum (20%)
            time_score * 0.15  # Time efficiency (15%)
        )
        
        # Apply learning curve adjustments
        if self.quizzes < 10:
            # New learners get a boost to avoid discouragement
            engagement_score = min(100, engagement_score * 1.1)
        elif self.quizzes > 50:
            # Experienced learners need higher standards
            engagement_score = engagement_score * 0.95
        
        # Update the stored engagement score
        self.engagement_score = min(100, max(0, engagement_score))
        
        # Determine engagement level with more nuanced thresholds
        if self.engagement_score >= 85:
            return "highly_engaged"
        elif self.engagement_score >= 70:
            return "engaged"
        elif self.engagement_score >= 55:
            return "moderate"
        elif self.engagement_score >= 35:
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
                      hints_used: int = 0, topic: str = "general", skipped: bool = False) -> None:
        """Record a complete learning session with detailed metrics and enhanced engagement tracking"""
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
        
        # Add enhanced session data
        session_data = asdict(session)
        session_data.update({
            "topic": topic,
            "skipped": skipped
        })
        
        self.learning_sessions.append(session_data)
        self.quizzes += 1
        self.total_response_time += response_time
        self.total_answer_changes += answer_changes
        self.total_hints_used += hints_used
        
        if correct:
            self.correct += 1
        if skipped:
            self.total_skipped += 1
            
        # Update topic preferences
        if topic not in self.topic_preferences:
            self.topic_preferences[topic] = {"total": 0, "correct": 0, "avg_time": 0}
        
        self.topic_preferences[topic]["total"] += 1
        if correct:
            self.topic_preferences[topic]["correct"] += 1
        self.topic_preferences[topic]["avg_time"] = (
            (self.topic_preferences[topic]["avg_time"] * (self.topic_preferences[topic]["total"] - 1) + response_time) 
            / self.topic_preferences[topic]["total"]
        )
        
        # Update difficulty progression
        self.difficulty_progression.append(difficulty)
        if len(self.difficulty_progression) > 20:  # Keep only recent 20
            self.difficulty_progression = self.difficulty_progression[-20:]
        
        # Update learning style based on patterns
        self._update_learning_style()
        
        # Update engagement metrics
        self._update_improvement_trend()
        self._update_engagement_score()
        
        self.last_activity = datetime.now().isoformat()
        self.save()

    def _update_improvement_trend(self):
        """Calculate improvement trend based on recent vs historical performance"""
        if len(self.learning_sessions) < 10:
            self.improvement_trend = 0.0
            return
            
        # Compare last 5 sessions vs previous 5 sessions
        recent_sessions = self.learning_sessions[-5:]
        previous_sessions = self.learning_sessions[-10:-5] if len(self.learning_sessions) >= 10 else self.learning_sessions[:-5]
        
        if not previous_sessions:
            self.improvement_trend = 0.0
            return
            
        recent_accuracy = sum(1 for s in recent_sessions if s.get('correct', False)) / len(recent_sessions)
        previous_accuracy = sum(1 for s in previous_sessions if s.get('correct', False)) / len(previous_sessions)
        
        self.improvement_trend = (recent_accuracy - previous_accuracy) * 100

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
        """Generate comprehensive insights for teachers/educators with enhanced engagement tracking"""
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
            "needs_attention": self.engagement_level in ["struggling", "moderate"] and self.accuracy < 0.5,
            # Enhanced engagement metrics
            "skip_rate": round(self.skip_rate * 100, 1),
            "hint_dependency": round(self.hint_dependency * 100, 1),
            "recent_performance": round(self.recent_performance * 100, 1),
            "consistency_score": round(self.consistency_score, 1),
            "learning_momentum": round(self.learning_momentum, 1),
            "improvement_trend": round(self.improvement_trend, 1),
            "topic_preferences": self.topic_preferences,
            "difficulty_progression": self.difficulty_progression[-10:] if self.difficulty_progression else [],
            # Engagement insights
            "engagement_insights": self._get_engagement_insights()
        }

    def _get_engagement_insights(self) -> dict:
        """Generate specific insights about student engagement patterns"""
        insights = {
            "strengths": [],
            "concerns": [],
            "recommendations": []
        }
        
        # Analyze strengths
        if self.accuracy > 0.8:
            insights["strengths"].append("High accuracy rate")
        if self.consistency_score > 80:
            insights["strengths"].append("Consistent performance")
        if self.learning_momentum > 10:
            insights["strengths"].append("Improving performance trend")
        if self.skip_rate < 0.1:
            insights["strengths"].append("Low skip rate - good persistence")
        if self.hint_dependency < 0.3:
            insights["strengths"].append("Independent problem solving")
        
        # Analyze concerns
        if self.skip_rate > 0.3:
            insights["concerns"].append("High skip rate - may indicate difficulty or disengagement")
        if self.hint_dependency > 0.7:
            insights["concerns"].append("Over-reliance on hints - may need confidence building")
        if self.hesitation_score > 2.0:
            insights["concerns"].append("High hesitation - may indicate uncertainty")
        if self.learning_momentum < -10:
            insights["concerns"].append("Declining performance trend")
        if self.consistency_score < 40:
            insights["concerns"].append("Inconsistent performance")
        
        # Generate recommendations
        if self.engagement_level == "disengaged":
            insights["recommendations"].append("Consider easier questions or different topics to rebuild confidence")
        elif self.engagement_level == "struggling":
            insights["recommendations"].append("Provide more hints and encouragement, consider breaking down complex topics")
        elif self.engagement_level == "moderate":
            insights["recommendations"].append("Mix of easy and challenging questions to maintain engagement")
        elif self.engagement_level == "engaged":
            insights["recommendations"].append("Continue current approach, gradually increase difficulty")
        elif self.engagement_level == "highly_engaged":
            insights["recommendations"].append("Provide advanced challenges and explore new topics")
        
        # Topic-specific recommendations
        if self.topic_preferences:
            best_topic = max(self.topic_preferences.items(), key=lambda x: x[1]["correct"] / x[1]["total"] if x[1]["total"] > 0 else 0)
            worst_topic = min(self.topic_preferences.items(), key=lambda x: x[1]["correct"] / x[1]["total"] if x[1]["total"] > 0 else 0)
            
            if best_topic[1]["total"] > 3:
                insights["recommendations"].append(f"Strong performance in {best_topic[0]} - use as confidence builder")
            if worst_topic[1]["total"] > 3:
                insights["recommendations"].append(f"Needs support in {worst_topic[0]} - consider additional practice")
        
        return insights

    def record(self, correct: bool) -> None:
        """Legacy method for backward compatibility"""
        self.record_session(0, "unknown", "", correct, 0.0)


if __name__ == "__main__":  # pragma: no cover
    # small manual test when executed directly
    print(call_llm([{"role": "user", "content": "Hello"}]))
