"""FastAPI interface for ThinkBot.

Serves quiz questions and records answers while using the Gemini API to
provide feedback. Designed for deployment on services like Vercel.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from main import StudentProfile, call_llm

# locate project root (one directory above this file)
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
QUESTIONS_FILE = DATA_DIR / "questions.json"
STATIC_DIR = ROOT_DIR / "static"

with QUESTIONS_FILE.open("r", encoding="utf-8") as fh:
    _raw_questions = json.load(fh)

QUESTIONS = {level: qs for level, qs in _raw_questions.items()}
QUESTION_INDEX = {
    q["id"]: {**q, "difficulty": level}
    for level, qs in QUESTIONS.items()
    for q in qs
}

app = FastAPI(title="ThinkBot API")

# serve static files and root index for convenience when deployed
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
def root() -> str:
    """Return the demo HTML page."""
    index_path = STATIC_DIR / "index.html"
    return index_path.read_text(encoding="utf-8")


def select_question(profile: StudentProfile, topic: str = None) -> dict:
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
    
    # Get all questions from the selected level
    available_questions = QUESTIONS[level].copy()
    
    # Filter by topic if specified
    if topic:
        topic_questions = [q for q in available_questions if q.get('topic') == topic]
        if topic_questions:
            available_questions = topic_questions
        else:
            # If no questions for this topic at this level, try other levels
            for other_level in ["easy", "medium", "hard"]:
                if other_level != level:
                    other_questions = [q for q in QUESTIONS[other_level] if q.get('topic') == topic]
                    if other_questions:
                        available_questions = other_questions
                        level = other_level
                        break
    
    # Avoid recently asked questions (last 10 questions)
    recent_question_ids = [s.get('question_id') for s in recent_sessions[-10:] if s.get('question_id')]
    available_questions = [q for q in available_questions if q['id'] not in recent_question_ids]
    
    # If no questions available after filtering, use all questions from level
    if not available_questions:
        available_questions = QUESTIONS[level]
    
    # Check if we're running low on questions (less than 5 available)
    if len(available_questions) < 5:
        # Generate new questions automatically
        try:
            generate_new_questions_auto(topic or "general", level)
            # Reload questions after generation
            load_questions()
            # Try to get questions again
            available_questions = QUESTIONS[level].copy()
            if topic:
                available_questions = [q for q in available_questions if q.get('topic') == topic]
            # Filter out recent questions again
            available_questions = [q for q in available_questions if q['id'] not in recent_question_ids]
        except Exception as e:
            print(f"Failed to generate new questions: {e}")
    
    # If still no questions available, use all questions from level
    if not available_questions:
        available_questions = QUESTIONS[level]
    
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
def get_question(student: str, topic: str = None):
    profile = StudentProfile.load(student)
    q = select_question(profile, topic)
    return {
        "id": q["id"],
        "question": q["question"],
        "difficulty": q["difficulty"],
        "topic": q.get("topic", "general"),
        "answer": q["answer"],
        "explanation": q.get("explanation", ""),
    }


@app.post("/answer")
def submit_answer(payload: AnswerPayload):
    profile = StudentProfile.load(payload.student)
    q = QUESTION_INDEX.get(payload.question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Unknown question")
    
    # More flexible answer matching
    def is_answer_correct(user_answer: str, correct_answer: str) -> bool:
        user_clean = user_answer.strip().lower()
        correct_clean = correct_answer.strip().lower()
        
        # Exact match
        if user_clean == correct_clean:
            return True
        
        # For numerical answers, be more strict - only allow exact matches or specific variations
        if user_clean.replace('.', '').replace('-', '').isdigit() or correct_clean.replace('.', '').replace('-', '').isdigit():
            # For numerical answers, only check exact match and specific variations
            # Don't use substring matching for numbers
            pass
        else:
            # For non-numerical answers, use substring matching
            # Check if user answer contains the correct answer (for cases like "Pacific Ocean" vs "Pacific")
            if correct_clean in user_clean:
                return True
                
            # Check if correct answer contains user answer (for cases like "Pacific" vs "Pacific Ocean")
            if user_clean in correct_clean:
                return True
            
        # Check for common variations
        variations = {
            "pacific ocean": ["pacific", "pacific ocean"],
            "atlantic ocean": ["atlantic", "atlantic ocean"],
            "indian ocean": ["indian", "indian ocean"],
            "arctic ocean": ["arctic", "arctic ocean"],
            "southern ocean": ["southern", "southern ocean"],
            "north america": ["north america", "north american"],
            "south america": ["south america", "south american"],
            "united states": ["usa", "us", "united states", "america"],
            "united kingdom": ["uk", "britain", "united kingdom", "england"],
            "25π": ["25pi", "25 pi", "25*π", "25 * π"],
            "36π": ["36pi", "36 pi", "36*π", "36 * π"],
            "10π": ["10pi", "10 pi", "10*π", "10 * π"],
            "a² + b² = c²": ["a^2 + b^2 = c^2", "a squared plus b squared equals c squared"],
            "0.625": ["625/1000", "5/8"],
            "5/6": ["10/12", "0.833"],
            "32": ["2^5", "2 to the power of 5"],
            "81": ["3^4", "3 to the power of 4"]
        }
        
        for correct_key, variants in variations.items():
            if correct_clean == correct_key:
                if user_clean in variants:
                    return True
            elif user_clean == correct_key:
                if correct_clean in variants:
                    return True
        
        return False
    
    correct = is_answer_correct(payload.answer, q["answer"])
    
    # Record comprehensive session data with enhanced engagement tracking
    profile.record_session(
        question_id=payload.question_id,
        difficulty=q["difficulty"],
        answer=payload.answer,
        correct=correct,
        response_time=payload.response_time,
        answer_changes=payload.answer_changes,
        hints_used=payload.hints_used,
        topic=q.get("topic", "general"),
        skipped=payload.answer.lower().strip() == "skip" or payload.answer.lower().strip() == ""
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
        "insights": profile.get_learning_insights()
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
    return profile.get_learning_insights()

@app.get("/analytics")
def get_all_analytics():
    """Get analytics for all students (teacher dashboard)."""
    import os
    from pathlib import Path
    
    analytics = []
    # Look for student files in the data directory (where StudentProfile saves them)
    data_dir = Path("data")
    
    if data_dir.exists():
        for file_path in data_dir.glob("student_*.json"):
            student_name = file_path.stem.replace("student_", "")
            try:
                profile = StudentProfile.load(student_name)
                insights = profile.get_learning_insights()
                # Ensure we have the student name in the insights
                insights["name"] = student_name
                analytics.append(insights)
            except Exception as e:
                print(f"Error loading profile for {student_name}: {e}")
                continue
    
    # If no student files found, return empty analytics
    if not analytics:
        return {
            "total_students": 0,
            "students": [],
            "summary": {
                "high_performers": 0,
                "struggling_students": 0,
                "average_accuracy": 0.0
            }
        }
    
    return {
        "total_students": len(analytics),
        "students": analytics,
        "summary": {
            "high_performers": len([s for s in analytics if s.get("accuracy", 0) > 0.8]),
            "struggling_students": len([s for s in analytics if s.get("needs_attention", False)]),
            "average_accuracy": sum(s.get("accuracy", 0) for s in analytics) / len(analytics) if analytics else 0
        }
    }


@app.delete("/clear-student/{student_name}")
def clear_student_data(student_name: str):
    """Clear all data for a specific student."""
    try:
        from pathlib import Path
        import os
        
        # Look for student file in the data directory
        data_dir = Path("data")
        student_file = data_dir / f"student_{student_name}.json"
        
        if student_file.exists():
            # Delete the student profile file
            student_file.unlink()
            return {"message": f"Successfully cleared data for student: {student_name}"}
        else:
            return {"message": f"No data found for student: {student_name}"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing student data: {str(e)}")

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

@app.post("/end-quiz-session")
def end_quiz_session(student: str):
    """End a quiz session for a student."""
    try:
        profile = StudentProfile.load(student)
        profile.end_quiz_session()
        return {"message": "Quiz session ended", "quiz_sessions": profile.quiz_sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ending quiz session: {str(e)}")

@app.post("/generate-questions")
def generate_new_questions(topic: str = None, count: int = 5):
    """Generate new questions using LLM API."""
    try:
        # Create a prompt for generating questions
        prompt = f"""
        Generate {count} educational quiz questions on the topic: {topic or 'general knowledge'}.
        Each question should be in JSON format with the following structure:
        {{
            "question": "The question text",
            "answer": "The correct answer",
            "topic": "{topic or 'general'}",
            "hint": "A helpful hint for the student",
            "difficulty": "easy|medium|hard"
        }}
        
        Make sure the questions are:
        - Educational and appropriate for students
        - Clear and unambiguous
        - Have single correct answers
        - Include helpful hints
        - Vary in difficulty levels
        
        Return only the JSON array, no other text.
        """
        
        # Call LLM to generate questions
        response = call_llm(prompt)
        
        # Parse the response (assuming it returns valid JSON)
        import json
        try:
            questions = json.loads(response)
            if not isinstance(questions, list):
                questions = [questions]
            
            # Add unique IDs and save to questions file
            new_questions = []
            max_id = max([q.get('id', 0) for level_questions in QUESTIONS.values() for q in level_questions], default=0)
            for i, q in enumerate(questions):
                q["id"] = max_id + i + 1
                new_questions.append(q)
            
            # Update the questions file
            difficulty = new_questions[0].get("difficulty", "medium")
            if difficulty not in QUESTIONS:
                QUESTIONS[difficulty] = []
            
            QUESTIONS[difficulty].extend(new_questions)
            
            # Update question index
            for q in new_questions:
                QUESTION_INDEX[q["id"]] = {**q, "difficulty": difficulty}
            
            # Save to file
            with QUESTIONS_FILE.open("w", encoding="utf-8") as fh:
                json.dump(QUESTIONS, fh, indent=2)
            
            return {
                "message": f"Generated {len(new_questions)} new questions",
                "questions": new_questions,
                "topic": topic or "general"
            }
            
        except json.JSONDecodeError:
            return {"error": "Failed to parse LLM response as JSON"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")


def generate_new_questions_auto(topic: str, level: str, count: int = 10):
    """Automatically generate new questions when the question bank runs low."""
    try:
        # Create a prompt for generating questions
        prompt = f"""Generate {count} new {level} difficulty quiz questions about {topic}. 
        Return as JSON array with this exact format:
        [
            {{
                "question": "Question text here?",
                "answer": "correct answer",
                "topic": "{topic}",
                "hint": "helpful hint for the student"
            }}
        ]
        
        Make questions educational, clear, and appropriate for {level} level.
        Ensure answers are concise and correct.
        Include variety in question types and formats."""
        
        # Call the LLM to generate questions
        response = call_llm(prompt)
        
        # Parse the JSON response
        if response.startswith('[') and response.endswith(']'):
            new_questions = json.loads(response)
            
            # Add unique IDs to the questions
            max_id = max([q.get('id', 0) for level_questions in QUESTIONS.values() for q in level_questions], default=0)
            for i, question in enumerate(new_questions):
                question['id'] = max_id + i + 1
            
            # Add to the appropriate level
            QUESTIONS[level].extend(new_questions)
            
            # Update question index
            for q in new_questions:
                QUESTION_INDEX[q["id"]] = {**q, "difficulty": level}
            
            # Save updated questions to file
            with QUESTIONS_FILE.open("w", encoding="utf-8") as fh:
                json.dump(QUESTIONS, fh, indent=2)
            
            print(f"Generated {len(new_questions)} new {level} questions for topic '{topic}'")
            return True
        else:
            print(f"Failed to parse LLM response for question generation: {response}")
            return False
            
    except Exception as e:
        print(f"Error generating new questions: {e}")
        return False


def load_questions():
    """Reload questions from JSON file."""
    global QUESTIONS, QUESTION_INDEX
    try:
        with QUESTIONS_FILE.open("r", encoding="utf-8") as fh:
            _raw_questions = json.load(fh)
        
        QUESTIONS = {level: qs for level, qs in _raw_questions.items()}
        QUESTION_INDEX = {
            q["id"]: {**q, "difficulty": level}
            for level, qs in QUESTIONS.items()
            for q in qs
        }
        return True
    except Exception as e:
        print(f"Error loading questions: {e}")
        return False
