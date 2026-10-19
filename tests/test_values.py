"""Slice 2: values must cite current statements only."""
from fastapi.testclient import TestClient

from server import ai, citations, main

client = TestClient(main.app)
STATEMENTS = [
    {"id": "S1", "title": "Career growth", "text": "Moving abroad could improve my career."},
    {"id": "S2", "title": "Family", "text": "I am worried about leaving my family."},
    {"id": "S4", "title": "Pay", "text": "San Francisco pays more."},  # S3 was removed by the person
]
REQ = {"decision": "Berlin or San Francisco?", "options": ["Berlin", "San Francisco"], "statements": STATEMENTS}


def test_validator_drops_uncited_unknown_and_removed():
    valid = {"S1", "S2", "S4"}
    out, removed = citations.validate_values(
        [
            {"name": "Career growth", "cites": ["S1"]},
            {"name": "Adventure", "cites": []},           # no citation
            {"name": "Weather", "cites": ["S9"]},         # invented ID
            {"name": "Friends", "cites": ["S2", "S3"]},   # cites a removed statement
            {"name": "career growth", "cites": ["S1"]},   # duplicate
            {"name": "Income", "cites": ["S4", "S4"]},
        ],
        valid,
    )
    assert [v["name"] for v in out] == ["Career growth", "Income"]
    assert out[1]["cites"] == ["S4"]
    assert removed == 4


def test_endpoint_returns_only_valid_values(monkeypatch):
    fake = {"values": [{"name": "Family nearby", "cites": ["S2"]}, {"name": "Climate", "cites": ["S3"]}], "crisis": False}
    seen = {}

    def fake_call(task, instr, payload, schema):
        seen["ids"] = [s["id"] for s in payload["STATEMENTS"]]
        return fake, None

    monkeypatch.setattr(ai, "call", fake_call)
    r = client.post("/api/values", json=REQ)
    assert r.status_code == 200
    assert r.json() == {"values": [{"name": "Family nearby", "cites": ["S2"]}], "crisis": False}
    assert seen["ids"] == ["S1", "S2", "S4"]  # removed statements are never sent


def test_crisis_in_edited_statement_stops_values(monkeypatch):
    monkeypatch.setattr(ai, "call", lambda *a, **k: (_ for _ in ()).throw(AssertionError("no AI call")))
    bad = STATEMENTS + [{"id": "S5", "title": "Hard times", "text": "Sometimes I think about ending my life."}]
    r = client.post("/api/values", json={**REQ, "statements": bad})
    assert r.json() == {"crisis": True}


def test_values_needs_a_statement():
    r = client.post("/api/values", json={**REQ, "statements": []})
    assert r.status_code == 422
