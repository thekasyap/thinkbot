import api
from fastapi.testclient import TestClient


def setup_stub(monkeypatch, accuracy=0.0):
    class StubProfile:
        def __init__(self):
            self.accuracy = accuracy
            self.records = []

        def record(self, correct):
            self.records.append(correct)
            if self.records:
                self.accuracy = sum(self.records) / len(self.records)

        @classmethod
        def load(cls, name):
            return cls()

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
    assert captured["msg"][0]["content"].startswith("Question")
