import api
from fastapi.testclient import TestClient


def setup_stub(monkeypatch, accuracy=0.0):
    class StubProfile:
        def __init__(self, name="test"):
            self.name = name
            self.accuracy = accuracy
            self.records = []
            self.learning_sessions = []
            self.engagement_level = "learning"
            self.learning_style = "unknown"
            self.learning_pace = "moderate"

        def record(self, correct):
            self.records.append(correct)
            if self.records:
                self.accuracy = sum(self.records) / len(self.records)

        def record_session(self, question_id, difficulty, answer, correct, response_time, answer_changes=0, hints_used=0):
            self.record(correct)

        def get_learning_insights(self):
            return {
                "student_name": "test",
                "total_quizzes": len(self.records),
                "accuracy": self.accuracy * 100,
                "learning_style": self.learning_style,
                "engagement_level": self.engagement_level,
                "learning_pace": self.learning_pace,
                "average_response_time": 0.0,
                "hesitation_score": 0.0,
                "engagement_score": 0.0,
                "last_activity": "",
                "needs_attention": False
            }

        @classmethod
        def load(cls, name):
            return cls(name)

    monkeypatch.setattr(api, "StudentProfile", StubProfile)
    return StubProfile


def test_get_question_respects_accuracy(monkeypatch):
    setup_stub(monkeypatch, accuracy=0.2)
    monkeypatch.setattr(api.random, "choice", lambda seq: seq[0])
    client = TestClient(api.app)
    res = client.get("/question", params={"student": "Alice"})
    assert res.status_code == 200
    data = res.json()
    assert data["difficulty"] == "easy"
    assert data["id"] == api.QUESTIONS["easy"][0]["id"]


def test_submit_answer_updates_accuracy(monkeypatch):
    setup_stub(monkeypatch, accuracy=0.0)
    captured = {}
    monkeypatch.setattr(api, "call_llm", lambda messages: captured.setdefault("msg", messages) or "Good job")
    client = TestClient(api.app)
    q = api.QUESTIONS["easy"][0]
    res = client.post(
        "/answer",
        json={"student": "Bob", "question_id": q["id"], "answer": q["answer"]},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["correct"] is True
    assert data["accuracy"] == 1.0
    assert "Student Profile:" in captured["msg"][0]["content"]


def test_root_serves_html():
    client = TestClient(api.app)
    res = client.get("/")
    assert res.status_code == 200
    assert "<!DOCTYPE html>" in res.text

