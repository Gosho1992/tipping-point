"""Slice 7: crisis wording stops every endpoint; no request text reaches the logs; security headers are set."""
import logging

import pytest
from fastapi.testclient import TestClient

from server import ai, main, safety

client = TestClient(main.app)
OPTS3 = [{"id": "A", "name": "Quit"}, {"id": "B", "name": "Stay"}, {"id": "W", "name": "Wait / neither"}]
OK_ST = [{"id": "S1", "title": "Manager", "text": "My manager shouts at me."}]
BAD_ST = OK_ST + [{"id": "S2", "title": "Hard", "text": "I keep thinking about killing myself."}]


@pytest.fixture
def no_ai(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("AI must not be called")
    monkeypatch.setattr(ai, "call", boom)


@pytest.mark.parametrize("phrase", [
    "I want to die", "I've thought about ending my life", "maybe I should kill myself", "I don’t want to live anymore",
    "I've been hurting myself", "self-harm", "I'm not safe at home",
])
def test_phrases_detected(phrase):
    assert safety.contains_crisis([phrase])


@pytest.mark.parametrize("ok", ["This job is killing my motivation", "I'd die for a week off", "dying to see Berlin"])
def test_ordinary_hyperbole_not_flagged(ok):
    assert not safety.contains_crisis([ok])


def test_crisis_in_edited_statement_stops_values(no_ai):
    r = client.post("/api/values", json={"decision": "Quit?", "options": ["Quit", "Stay"], "statements": BAD_ST})
    assert r.json() == {"crisis": True}


def test_crisis_in_value_name_stops_scores(no_ai):
    r = client.post("/api/scores", json={"options": OPTS3, "values": [{"id": "V1", "name": "Wanting to die"}], "statements": OK_ST})
    assert r.json() == {"crisis": True}


def test_crisis_in_statement_stops_scores(no_ai):
    r = client.post("/api/scores", json={"options": OPTS3, "values": [{"id": "V1", "name": "Respect"}], "statements": BAD_ST})
    assert r.json() == {"crisis": True}


def test_crisis_in_statement_stops_futures(no_ai):
    r = client.post("/api/futures", json={"options": OPTS3, "statements": BAD_ST})
    assert r.json() == {"crisis": True}


@pytest.mark.parametrize("path,body", [
    ("/api/scores", {"options": OPTS3, "values": [{"id": "V1", "name": "Respect"}], "statements": OK_ST}),
    ("/api/futures", {"options": OPTS3, "statements": OK_ST}),
])
def test_model_crisis_flag_stops(monkeypatch, path, body):
    monkeypatch.setattr(ai, "call", lambda *a, **k: ({"cells": [], "cards": [], "crisis": True}, None))
    assert client.post(path, json=body).json() == {"crisis": True}


def test_oversized_body_is_413():
    r = client.post("/api/futures", content=b"x" * (65 * 1024), headers={"content-type": "application/json"})
    assert r.status_code == 413 and r.json() == {"code": "too_large"}


def test_no_request_text_in_logs(monkeypatch, caplog):
    secret = "MY-PRIVATE-WORDS-123"
    monkeypatch.setattr(ai, "call", lambda *a, **k: ({"cards": [{"option": "A", "sentences": [{"text": secret, "cites": ["S1"]}]}], "crisis": False}, None))
    with caplog.at_level(logging.DEBUG):
        client.post("/api/futures", json={"options": OPTS3, "statements": [{"id": "S1", "title": secret, "text": secret}]})
        client.post("/api/futures", json={"options": OPTS3, "statements": [{"id": "S1", "title": "x" * 90, "text": secret}]})  # rejected input
    assert secret not in caplog.text


def test_security_headers_on_page():
    r = client.get("/")
    assert r.status_code == 200
    assert "script-src 'self'" in r.headers["content-security-policy"]
    assert r.headers["x-content-type-options"] == "nosniff"
