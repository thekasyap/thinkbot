import json
from pathlib import Path

import main


def test_record_and_accuracy(tmp_path, monkeypatch):
    # Redirect data directory to a temp path to avoid touching real files
    monkeypatch.setattr(main, "DATA_DIR", tmp_path)

    profile = main.StudentProfile.load("Alice")
    assert profile.accuracy == 0.0
    profile.record(True)
    assert profile.quizzes == 1
    assert profile.correct == 1
    assert profile.accuracy == 1.0
    profile.record(False)
    assert profile.quizzes == 2
    assert profile.correct == 1
    assert profile.accuracy == 0.5

    # verify file written
    data = json.loads((tmp_path / "student_Alice.json").read_text())
    assert data["correct"] == 1
    assert data["quizzes"] == 2
