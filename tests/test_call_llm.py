import types as pytypes

import main


class DummyClient:
    def __init__(self, captured):
        self.captured = captured

        class Models:
            def __init__(self, outer):
                self.outer = outer

            def generate_content(self, **kwargs):
                outer = self.outer
                outer.captured.update(kwargs)
                return pytypes.SimpleNamespace(text="Hello")

        self.models = Models(self)


def test_call_llm(monkeypatch):
    captured = {}
    monkeypatch.setattr(main, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(main.genai, "Client", lambda api_key=None: DummyClient(captured))

    result = main.call_llm([{"role": "user", "content": "hi"}])
    assert result == "Hello"
    assert captured["model"] == main.GEMINI_MODEL
    assert captured["config"].thinking_config.thinking_budget == 0
    assert captured["contents"][0].role == "user"


def test_call_llm_without_key(monkeypatch):
    monkeypatch.setattr(main, "GEMINI_API_KEY", "")
    result = main.call_llm([{"role": "user", "content": "hi"}])
    assert "key" in result.lower()
