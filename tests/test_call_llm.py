import main


def test_call_llm(monkeypatch):
    captured = {}

    def fake_post(url, params=None, json=None, timeout=None):
        captured.update({"url": url, "params": params, "json": json})

        class Resp:
            def raise_for_status(self):
                pass

            def json(self):
                return {"candidates": [{"content": {"parts": [{"text": "Hello"}]}}]}

        return Resp()

    monkeypatch.setattr(main, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(main.requests, "post", fake_post)

    result = main.call_llm([{"role": "user", "content": "hi"}])
    assert result == "Hello"
    assert "thinkingBudget" in captured["json"]["generationConfig"]["thinkingConfig"]
    assert captured["json"]["contents"][0]["role"] == "user"


def test_call_llm_without_key(monkeypatch):
    monkeypatch.setattr(main, "GEMINI_API_KEY", "")
    result = main.call_llm([{"role": "user", "content": "hi"}])
    assert "key" in result.lower()
