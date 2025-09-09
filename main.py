"""ThinkBot: A simple adaptive tutor using the Gemini API and JSON storage.

This script provides two commands:

* ``ingest <pdf>`` - load a PDF into the local knowledge base.
* ``chat <student_name>`` - start an interactive tutoring session.

The tutor talks to Google's `gemini-2.5-flash` model via the official
`google-genai` SDK. Set the ``GEMINI_API_KEY`` environment variable before
running the script.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List

import numpy as np
from google import genai
from google.genai import types
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATA_DIR = Path("data")
KNOWLEDGE_FILE = DATA_DIR / "knowledge.json"
EMBED_MODEL = "all-MiniLM-L6-v2"

# Gemini configuration
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def ensure_data_dir() -> None:
    """Ensure the data directory exists."""
    DATA_DIR.mkdir(exist_ok=True)


def load_json(path: Path, default):
    if path.exists():
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    return default


def save_json(path: Path, data) -> None:
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


# ---------------------------------------------------------------------------
# Knowledge base (very small JSON based vector store)
# ---------------------------------------------------------------------------

def load_knowledge() -> List[dict]:
    data = load_json(KNOWLEDGE_FILE, {"chunks": []})
    return data["chunks"]


def save_knowledge(chunks: List[dict]) -> None:
    save_json(KNOWLEDGE_FILE, {"chunks": chunks})


def embed_texts(texts: List[str]) -> List[List[float]]:
    model = SentenceTransformer(EMBED_MODEL)
    vectors = model.encode(texts, show_progress_bar=False)
    return [vec.tolist() for vec in vectors]


def ingest_pdf(pdf_path: str) -> None:
    """Parse a PDF, chunk text and store embeddings."""
    ensure_data_dir()
    reader = PdfReader(pdf_path)
    full_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    words = full_text.split()
    chunk_size = 200  # words
    chunks = [" ".join(words[i : i + chunk_size]) for i in range(0, len(words), chunk_size) if words[i : i + chunk_size]]
    embeddings = embed_texts(chunks)
    kb_chunks = load_knowledge()
    for text, emb in zip(chunks, embeddings):
        kb_chunks.append({"text": text, "embedding": emb})
    save_knowledge(kb_chunks)
    print(f"Ingested {len(chunks)} chunks into the knowledge base.")


def retrieve(query: str, k: int = 3) -> List[str]:
    chunks = load_knowledge()
    if not chunks:
        return []
    model = SentenceTransformer(EMBED_MODEL)
    q_emb = model.encode([query])[0]
    # compute cosine similarity
    chunk_embs = np.array([c["embedding"] for c in chunks])
    scores = chunk_embs @ q_emb / (np.linalg.norm(chunk_embs, axis=1) * np.linalg.norm(q_emb) + 1e-9)
    top_indices = scores.argsort()[-k:][::-1]
    return [chunks[i]["text"] for i in top_indices]


# ---------------------------------------------------------------------------
# LLM client
# ---------------------------------------------------------------------------

def call_llm(messages: List[dict]) -> str:
    """Call the Gemini API and return the text response.

    ``messages`` follows the OpenAI-style ``{"role": ..., "content": ...}`` format.
    The function converts it to the Gemini ``contents`` structure.
    """

    if not GEMINI_API_KEY:
        return "[Gemini API key not set]"

    contents = [
        types.Content(role=m["role"], parts=[types.Part.from_text(text=m["content"])])
        for m in messages
    ]

    client = genai.Client(api_key=GEMINI_API_KEY)

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            ),
        )
        return response.text.strip()
    except Exception as exc:  # pragma: no cover - networking
        return f"[Error contacting LLM: {exc}]"


# ---------------------------------------------------------------------------
# Student profile handling
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
        ensure_data_dir()
        save_json(self.path, asdict(self))

    @classmethod
    def load(cls, name: str) -> "StudentProfile":
        ensure_data_dir()
        data = load_json(DATA_DIR / f"student_{name}.json", None)
        if data:
            return cls(**data)
        return cls(name=name)

    def record(self, correct: bool) -> None:
        self.quizzes += 1
        if correct:
            self.correct += 1
        self.save()


# ---------------------------------------------------------------------------
# Chat logic
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are ThinkBot, an adaptive teaching assistant."
    " Use the provided context to answer questions."
    " Speak clearly and educationally."
)


def generate_quiz(context: str) -> str:
    prompt = f"Create a single short quiz question based on: {context}".strip()
    return call_llm([{"role": "user", "content": prompt}])


def grade_answer(question: str, answer: str) -> tuple[bool, str]:
    prompt = (
        f"Question: {question}\n"
        f"Student answer: {answer}\n"
        "Respond with 'correct' or 'incorrect' followed by a short explanation."
    )
    result = call_llm([{"role": "user", "content": prompt}])
    is_correct = result.lower().startswith("correct")
    return is_correct, result


def chat(student_name: str) -> None:
    profile = StudentProfile.load(student_name)
    print(f"Starting session for {student_name}. Type 'exit' to end.")
    turns = 0
    while True:
        user_input = input("You: ")
        if user_input.strip().lower() == "exit":
            break
        turns += 1
        context = "\n".join(retrieve(user_input))
        adapt = "" if profile.accuracy >= 0.5 else " Use simple language and more examples."
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT + adapt + f"\nContext:\n{context}"},
            {"role": "user", "content": user_input},
        ]
        reply = call_llm(messages)
        print(f"Tutor: {reply}")

        # Random quiz every 3 turns on average
        if random.random() < 1 / 3:
            quiz_context = context or "general knowledge from the lesson"
            question = generate_quiz(quiz_context)
            print(f"\nQuiz: {question}")
            answer = input("Your answer: ")
            correct, feedback = grade_answer(question, answer)
            profile.record(correct)
            print(f"Tutor: {feedback}\n")

    if profile.quizzes:
        print(
            f"Session complete. Score: {profile.correct}/{profile.quizzes}"
            f" ({profile.accuracy*100:.1f}% correct)."
        )
    profile.save()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ThinkBot adaptive tutor")
    sub = parser.add_subparsers(dest="command")

    p_ingest = sub.add_parser("ingest", help="Add a PDF to the knowledge base")
    p_ingest.add_argument("pdf", help="Path to PDF file")

    p_chat = sub.add_parser("chat", help="Start a tutoring session")
    p_chat.add_argument("student", help="Student name")

    args = parser.parse_args(argv)

    if args.command == "ingest":
        ingest_pdf(args.pdf)
    elif args.command == "chat":
        chat(args.student)
    else:
        parser.print_help()
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

