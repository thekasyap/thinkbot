"""FastAPI interface for ThinkBot.

Serves quiz questions and records answers while using the Gemini API to
provide feedback. Designed for deployment on services like Vercel.
"""
from __future__ import annotations

import json
import random
import re
from pathlib import Path
from fractions import Fraction
from decimal import Decimal, InvalidOperation

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from main import StudentProfile, call_llm

DATA_DIR = Path(__file__).parent / "data"
QUESTIONS_FILE = DATA_DIR / "questions.json"

with QUESTIONS_FILE.open("r", encoding="utf-8") as fh:
    _raw_questions = json.load(fh)

QUESTIONS = {level: qs for level, qs in _raw_questions.items()}
QUESTION_INDEX = {
    q["id"]: {**q, "difficulty": level}
    for level, qs in QUESTIONS.items()
    for q in qs
}

app = FastAPI(title="ThinkBot API")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve the main HTML file at the root
@app.get("/")
def read_root():
    with open("static/index.html", "r") as f:
        return HTMLResponse(f.read())

@app.get("/test-math")
def test_math():
    result = is_mathematically_equivalent("0.5", "1/2")
    return {"test": "0.5 == 1/2", "result": result}


def normalize_answer(answer: str) -> str:
    """Normalize answer for comparison by removing extra spaces and converting to lowercase."""
    return answer.strip().lower()

def is_mathematically_equivalent(answer1: str, answer2: str) -> bool:
    """Check if two answers are mathematically equivalent."""
    # First try exact string match (case insensitive)
    if normalize_answer(answer1) == normalize_answer(answer2):
        return True
    
    # Try to convert both to numbers and compare
    try:
        # Handle fractions like "1/2", "1/3", etc.
        if '/' in answer1 and '/' in answer2:
            frac1 = Fraction(answer1)
            frac2 = Fraction(answer2)
            return frac1 == frac2
        
        # Handle decimal numbers
        try:
            dec1 = Decimal(answer1)
            dec2 = Decimal(answer2)
            return dec1 == dec2
        except (InvalidOperation, ValueError):
            pass
        
        # Try converting one to fraction and one to decimal
        if '/' in answer1:
            frac1 = Fraction(answer1)
            try:
                dec2 = Decimal(answer2)
                return float(frac1) == float(dec2)
            except (InvalidOperation, ValueError):
                pass
        elif '/' in answer2:
            frac2 = Fraction(answer2)
            try:
                dec1 = Decimal(answer1)
                return float(dec1) == float(frac2)
            except (InvalidOperation, ValueError):
                pass
        
        # Try converting both to float for comparison
        try:
            float1 = float(answer1)
            float2 = float(answer2)
            return abs(float1 - float2) < 1e-10  # Use small epsilon for floating point comparison
        except (ValueError, TypeError):
            pass
            
    except (ValueError, TypeError, ZeroDivisionError):
        pass
    
    return False

def select_question(profile: StudentProfile) -> dict:
    """Select a question with sophisticated adaptation logic."""
    # Get recent performance (last 5 questions)
    recent_sessions = profile.learning_sessions[-5:] if len(profile.learning_sessions) >= 5 else profile.learning_sessions
    recent_accuracy = sum(1 for s in recent_sessions if s['correct']) / len(recent_sessions) if recent_sessions else profile.accuracy
    
    # Consider engagement level and learning pace
    engagement = profile.engagement_level
    pace = profile.learning_pace
    
    # Adaptive difficulty selection
    if engagement == "struggling" or recent_accuracy < 0.3:
        level = "easy"
    elif engagement == "highly_engaged" and recent_accuracy > 0.8:
        level = "hard"
    elif pace == "fast" and recent_accuracy > 0.7:
        level = "hard"
    elif pace == "slow" and recent_accuracy < 0.6:
        level = "easy"
    else:
        level = "medium"
    
    # Select question based on learning style and topic preferences
    available_questions = QUESTIONS[level]
    
    # If we have topic preferences, try to match them
    if hasattr(profile, 'preferred_topics') and profile.preferred_topics:
        topic_questions = [q for q in available_questions if q.get('topic') in profile.preferred_topics]
        if topic_questions:
            available_questions = topic_questions
    
    q = random.choice(available_questions)
    return {**q, "difficulty": level}


class AnswerPayload(BaseModel):
    student: str
    question_id: int
    answer: str
    response_time: float = 0.0
    answer_changes: int = 0
    hints_used: int = 0


@app.get("/question")
def get_question(student: str):
    profile = StudentProfile.load(student)
    q = select_question(profile)
    return {
        "id": q["id"],
        "question": q["question"],
        "difficulty": q["difficulty"],
    }


@app.post("/answer")
def submit_answer(payload: AnswerPayload):
    profile = StudentProfile.load(payload.student)
    q = QUESTION_INDEX.get(payload.question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Unknown question")
    
    correct = is_mathematically_equivalent(payload.answer, q["answer"])
    print(f"DEBUG: Comparing '{payload.answer}' with '{q['answer']}' -> {correct}")
    
    # Record comprehensive session data
    profile.record_session(
        question_id=payload.question_id,
        difficulty=q["difficulty"],
        answer=payload.answer,
        correct=correct,
        response_time=payload.response_time,
        answer_changes=payload.answer_changes,
        hints_used=payload.hints_used
    )
    
    # Generate personalized feedback based on learning profile
    feedback = generate_personalized_feedback(profile, q, payload, correct)
    
    # Determine next action based on performance
    next_action = determine_next_action(profile, correct)
    
    return {
        "correct": correct,
        "feedback": feedback,
        "accuracy": profile.accuracy,
        "engagement_level": profile.engagement_level,
        "learning_style": profile.learning_style,
        "next_action": next_action,
        "hint": q.get("hint", ""),
        "insights": profile.get_learning_insights(),
    }

def generate_personalized_feedback(profile: StudentProfile, question: dict, payload: AnswerPayload, correct: bool) -> str:
    """Generate personalized feedback based on student profile and performance."""
    
    # Base prompt with context
    base_context = f"""
    Student Profile:
    - Name: {profile.name}
    - Learning Style: {profile.learning_style}
    - Engagement Level: {profile.engagement_level}
    - Learning Pace: {profile.learning_pace}
    - Current Accuracy: {profile.accuracy:.1%}
    - Response Time: {payload.response_time:.1f} seconds
    - Hints Used: {payload.hints_used}
    
    Question: {question['question']}
    Student Answer: {payload.answer}
    Correct Answer: {question['answer']}
    Difficulty: {question['difficulty']}
    Topic: {question.get('topic', 'general')}
    """
    
    if correct:
        # Positive feedback based on performance
        if profile.engagement_level == "highly_engaged":
            prompt = base_context + "\nProvide enthusiastic, challenging feedback that encourages deeper learning."
        elif profile.engagement_level == "struggling":
            prompt = base_context + "\nProvide gentle, encouraging feedback that builds confidence."
        else:
            prompt = base_context + "\nProvide positive, motivating feedback that encourages continued learning."
    else:
        # Constructive feedback for incorrect answers
        if profile.engagement_level == "struggling":
            prompt = base_context + "\nProvide gentle, step-by-step guidance without being discouraging. Focus on the learning process."
        elif profile.learning_style == "visual":
            prompt = base_context + "\nProvide visual learning hints and encourage drawing or diagramming the solution."
        elif profile.learning_style == "kinesthetic":
            prompt = base_context + "\nSuggest hands-on activities or practical examples to understand the concept."
        else:
            prompt = base_context + "\nProvide clear, detailed explanation of the correct approach and encourage trying again."
    
    return call_llm([{"role": "user", "content": prompt}])

def determine_next_action(profile: StudentProfile, correct: bool) -> str:
    """Determine the next learning action based on student performance."""
    
    if profile.engagement_level == "struggling":
        if correct:
            return "encouraged_practice"  # Continue with easier questions
        else:
            return "guided_learning"  # Provide more hints and guidance
    
    elif profile.engagement_level == "highly_engaged":
        if correct:
            return "challenge_mode"  # Offer harder questions or bonus challenges
        else:
            return "focused_review"  # Review the concept with detailed explanation
    
    elif profile.learning_pace == "fast" and correct:
        return "accelerated_learning"  # Move to next topic or harder questions
    
    elif profile.learning_pace == "slow" and not correct:
        return "reinforcement"  # Provide more practice with similar questions
    
    else:
        return "continue_learning"  # Normal progression

@app.get("/analytics/{student}")
def get_student_analytics(student: str):
    """Get comprehensive learning analytics for a student."""
    profile = StudentProfile.load(student)
    insights = profile.get_learning_insights()
    
    # Add enhanced learning style analysis
    learning_style_analysis = profile.get_learning_style_analysis()
    insights['learning_style_analysis'] = learning_style_analysis
    
    return insights


@app.get("/analytics")
def get_all_analytics():
    """Get analytics for all students (teacher dashboard)."""
    import os
    from pathlib import Path
    
    analytics = []
    data_dir = Path("data")
    
    if data_dir.exists():
        for file_path in data_dir.glob("student_*.json"):
            student_name = file_path.stem.replace("student_", "")
            profile = StudentProfile.load(student_name)
            analytics.append(profile.get_learning_insights())
    
    return {
        "total_students": len(analytics),
        "students": analytics,
        "summary": {
            "high_performers": len([s for s in analytics if s["accuracy"] > 80]),
            "struggling_students": len([s for s in analytics if s["needs_attention"]]),
            "average_accuracy": sum(s["accuracy"] for s in analytics) / len(analytics) if analytics else 0
        }
    }

@app.get("/hint/{question_id}")
def get_hint(question_id: int):
    """Get a hint for a specific question."""
    q = QUESTION_INDEX.get(question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return {
        "question_id": question_id,
        "hint": q.get("hint", "No hint available"),
        "topic": q.get("topic", "general")
    }

@app.get("/test-simple")
def test_simple():
    """Simple test endpoint."""
    return {"message": "Simple test works"}

@app.get("/learning-style/{student}")
def get_learning_style_analysis(student: str):
    """Get detailed learning style analysis for a student."""
    try:
        profile = StudentProfile.load(student)
        return profile.get_learning_style_analysis()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing learning style: {str(e)}")


