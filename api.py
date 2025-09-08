"""FastAPI interface for ThinkBot.

Serves quiz questions and records answers while using the Gemini API to
provide feedback. Designed for deployment on services like Vercel.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

from fastapi import FastAPI, HTTPException
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


def select_question(profile: StudentProfile) -> dict:
    """Select a question difficulty based on student accuracy."""
    if profile.accuracy > 0.8:
        level = "hard"
    elif profile.accuracy < 0.5:
        level = "easy"
    else:
        level = "medium"
    q = random.choice(QUESTIONS[level])
    return {**q, "difficulty": level}


class AnswerPayload(BaseModel):
    student: str
    question_id: int
    answer: str


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
    correct = payload.answer.strip().lower() == q["answer"].strip().lower()
    profile.record(correct)
    prompt = (
        f"Question: {q['question']}\n"
        f"Student answer: {payload.answer}\n"
        f"Correct answer: {q['answer']}\n"
        "Provide a short, encouraging explanation."
    )
    feedback = call_llm([{"role": "user", "content": prompt}])
    return {"correct": correct, "feedback": feedback, "accuracy": profile.accuracy}

