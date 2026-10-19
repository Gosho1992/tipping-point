"""Slice 5: future cards keep only sentences backed by current statements."""
from fastapi.testclient import TestClient

from server import ai, citations, main

client = TestClient(main.app)


def test_uncited_sentences_removed_and_cards_complete():
    cards, removed = citations.validate_futures(
        [
            {"option": "A", "sentences": [
                {"text": "You call your mother on the way home.", "cites": ["S2"]},
                {"text": "You live in a lovely flat in Kreuzberg.", "cites": []},      # invented, uncited
                {"text": "Your manager praises you.", "cites": ["S9"]},              # unknown ID
            ]},
            {"option": "B", "sentences": [{"text": "Nothing backed.", "cites": ["S7"]}]},
            {"option": "A", "sentences": [{"text": "duplicate card", "cites": ["S1"]}]},
        ],
        ["A", "B", "W"], {"S1", "S2"},
    )
    assert cards == [
        {"option": "A", "sentences": [{"text": "You call your mother on the way home.", "cites": ["S2"]}]},
        {"option": "B", "sentences": []},
        {"option": "W", "sentences": []},
    ]
    assert removed == 3


def test_futures_endpoint(monkeypatch):
    monkeypatch.setattr(ai, "call", lambda *a, **k: ({"cards": [{"option": "W", "sentences": [{"text": "You stay.", "cites": ["S1"]}]}], "crisis": False}, None))
    r = client.post("/api/futures", json={
        "options": [{"id": "A", "name": "Berlin"}, {"id": "B", "name": "SF"}, {"id": "W", "name": "Wait / neither"}],
        "statements": [{"id": "S1", "title": "Stable job", "text": "My current job is stable."}],
    })
    assert r.status_code == 200 and len(r.json()["cards"]) == 3
    assert r.json()["cards"][2]["sentences"][0]["cites"] == ["S1"]
