"""Interview turns: quote traceability, ID renumbering, live themes and grid, and the crisis stop."""
from fastapi.testclient import TestClient

from server import ai, citations, main

client = TestClient(main.app)

OPTIONS = [{"id": "A", "name": "Berlin"}, {"id": "B", "name": "San Francisco"}, {"id": "W", "name": "Wait / neither"}]
BASE = {
    "decision": "Should I move to Berlin or San Francisco?",
    "options": OPTIONS,
    "asked": [],
    "question": "Why does this decision matter to you right now?",
    "statements": [{"id": "S1", "title": "Career", "text": "Moving abroad could improve my career."}],
    "next_number": 2,
}
ANSWER = "Berlin is closer to my family, and that matters to me. San Francisco pays more."


def test_quote_must_appear_in_answer():
    answer = "I want to move abroad because it could improve my career, but I am worried about leaving my family."
    assert citations.quote_in_answer("it could improve my career", answer)
    assert citations.quote_in_answer("  It Could   improve my career. ", answer)
    assert not citations.quote_in_answer("my career would explode", answer)
    assert not citations.quote_in_answer("my", answer)


def test_renumber_new_statements():
    new, mapping, mm = citations.renumber_new(
        [
            {"id": "N1", "title": "Family", "text": "Family matters.", "quote": "Berlin is closer to my family"},
            {"id": "N2", "title": "", "text": "", "quote": ""},                       # empty: dropped, no ID used
            {"id": "N3", "title": "Pay", "text": "SF pays more.", "quote": "higher salary"},  # quote not in answer
        ],
        ANSWER, 5,
    )
    assert [s["id"] for s in new] == ["S5", "S6"]
    assert mapping == {"N1": "S5", "N3": "S6"}
    assert new[0]["quoteVerified"] is True and new[1]["quoteVerified"] is False and mm == 1


def test_themes_validated_and_mapped():
    themes, removed = citations.validate_themes(
        [
            {"id": "T1", "name": "Family nearby", "cites": ["N1"]},
            {"id": "T2", "name": "Career", "cites": ["S1", "N9"]},   # N9 never existed
            {"id": "T3", "name": "Weather", "cites": []},
            {"id": "T1", "name": "Dup id", "cites": ["S1"]},
        ],
        {"S1", "S5"}, {"N1": "S5"},
    )
    assert themes == [{"id": "T1", "name": "Family nearby", "cites": ["S5"]}]
    assert removed == 3


def fake_turn(data):
    return lambda *a, **k: (data, None)


def test_turn_returns_live_picture(monkeypatch):
    data = {
        "statements": [{"id": "N1", "title": "Family nearby", "text": "Being close to family matters to me.", "quote": "Berlin is closer to my family"},
                       {"id": "N2", "title": "Pay", "text": "San Francisco pays more.", "quote": "San Francisco pays more"}],
        "themes": [{"id": "T1", "name": "Family", "cites": ["N1"]}, {"id": "T2", "name": "Income", "cites": ["N2"]},
                   {"id": "T3", "name": "Career", "cites": ["S1"]}],
        "cells": [{"option": "A", "theme": "T1", "score": 8, "cites": ["N1"], "depends_on_others": False},
                  {"option": "B", "theme": "T2", "score": 9, "cites": ["N2"], "depends_on_others": False},
                  {"option": "B", "theme": "T1", "score": 7, "cites": ["S9"], "depends_on_others": False}],  # bad cite
        "next_question": "What would you lose by waiting?",
        "crisis": False,
    }
    monkeypatch.setattr(ai, "call", fake_turn(data))
    body = client.post("/api/turn", json={**BASE, "answer": ANSWER}).json()
    assert [s["id"] for s in body["statements"]] == ["S2", "S3"]
    assert [t["cites"] for t in body["themes"]] == [["S2"], ["S3"], ["S1"]]
    assert len(body["cells"]) == 9  # 3 options x 3 themes, always complete
    by = {(c["option"], c["value"]): c for c in body["cells"]}
    assert by[("A", "T1")]["score"] == 8 and by[("A", "T1")]["cites"] == ["S2"]
    assert by[("B", "T1")]["insufficient"] is True and by[("B", "T1")]["score"] is None
    assert "reason" not in by[("A", "T1")]
    assert body["next_question"] == "What would you lose by waiting?"


def test_crisis_phrase_stops_turn_without_calling_ai(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("AI must not be called")

    monkeypatch.setattr(ai, "call", boom)
    r = client.post("/api/turn", json={**BASE, "answer": "Honestly some days I want to die."})
    assert r.status_code == 200 and r.json() == {"crisis": True}


def test_model_crisis_flag_stops_turn(monkeypatch):
    monkeypatch.setattr(ai, "call", fake_turn({"statements": [], "themes": [], "cells": [], "next_question": "x", "crisis": True}))
    r = client.post("/api/turn", json={**BASE, "answer": "Everything feels pointless lately."})
    assert r.json() == {"crisis": True}


def test_ai_failure_is_502(monkeypatch):
    def fail(*a, **k):
        raise ai.AIError("timeout", maybe_billed=True)

    monkeypatch.setattr(ai, "call", fail)
    r = client.post("/api/turn", json={**BASE, "answer": "Something ordinary."})
    assert r.status_code == 502 and r.json() == {"code": "ai_failed"}


def test_too_long_answer_is_413():
    r = client.post("/api/turn", json={**BASE, "answer": "a" * 1501})
    assert r.status_code == 413 and r.json() == {"code": "too_large"}
