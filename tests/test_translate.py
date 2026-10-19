"""Voice translation endpoint: crisis stop, failure handling, and the same spend pipeline."""
from fastapi.testclient import TestClient

from server import ai, main

client = TestClient(main.app)


def test_translation_returned(monkeypatch):
    monkeypatch.setattr(ai, "call", lambda *a, **k: ({"translated_text": "I miss talking to him openly.", "crisis": False}, None))
    r = client.post("/api/translate", json={"text": "مجھے اس سے کھل کر بات کرنا یاد آتا ہے", "language": "Urdu"})
    assert r.status_code == 200 and r.json() == {"translated_text": "I miss talking to him openly.", "crisis": False}


def test_crisis_in_translation_stops(monkeypatch):
    monkeypatch.setattr(ai, "call", lambda *a, **k: ({"translated_text": "Sometimes I want to die.", "crisis": False}, None))
    assert client.post("/api/translate", json={"text": "...", "language": "Urdu"}).json() == {"crisis": True}


def test_model_crisis_flag_stops(monkeypatch):
    monkeypatch.setattr(ai, "call", lambda *a, **k: ({"translated_text": "x", "crisis": True}, None))
    assert client.post("/api/translate", json={"text": "...", "language": "Urdu"}).json() == {"crisis": True}


def test_empty_translation_is_failure(monkeypatch):
    monkeypatch.setattr(ai, "call", lambda *a, **k: ({"translated_text": "  ", "crisis": False}, None))
    r = client.post("/api/translate", json={"text": "...", "language": "Urdu"})
    assert r.status_code == 502 and r.json() == {"code": "ai_failed"}


def test_too_long_is_413():
    r = client.post("/api/translate", json={"text": "a" * 1501, "language": "Urdu"})
    assert r.status_code == 413
