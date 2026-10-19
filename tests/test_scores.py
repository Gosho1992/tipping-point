"""Slice 3: the score grid is always complete; unsupported cells become explicit insufficient cells."""
from fastapi.testclient import TestClient

from server import ai, citations, main

client = TestClient(main.app)


def test_grid_complete_and_bad_cells_converted():
    cells, changed = citations.validate_cells(
        [
            {"option": "A", "value": "V1", "score": 7, "reason": "Closer to family.", "cites": ["S2"], "depends_on_others": False},
            {"option": "A", "value": "V2", "score": 9, "reason": "Invented.", "cites": [], "depends_on_others": False},   # no cite
            {"option": "B", "value": "V1", "score": 4, "reason": "x", "cites": ["S9"], "depends_on_others": False},       # unknown ID
            {"option": "B", "value": "V2", "score": 11, "reason": "x", "cites": ["S1"], "depends_on_others": False},      # out of range
            {"option": "W", "value": "V1", "score": None, "reason": "", "cites": [], "depends_on_others": False},         # honest unknown
            {"option": "Z", "value": "V1", "score": 5, "reason": "x", "cites": ["S1"], "depends_on_others": False},       # unknown option
            {"option": "A", "value": "V1", "score": 1, "reason": "dup", "cites": ["S1"], "depends_on_others": False},     # duplicate
        ],
        ["A", "B", "W"], ["V1", "V2"], {"S1", "S2"},
    )
    assert len(cells) == 6
    by = {(c["option"], c["value"]): c for c in cells}
    assert by[("A", "V1")]["score"] == 7 and by[("A", "V1")]["insufficient"] is False
    for k in [("A", "V2"), ("B", "V1"), ("B", "V2"), ("W", "V1"), ("W", "V2")]:
        assert by[k] == {"option": k[0], "value": k[1], "score": None, "reason": "", "cites": [], "depends_on_others": False, "insufficient": True}
    assert changed == 4  # 3 converted + 1 missing (W,V2)


def test_bool_is_not_a_score():
    cells, _ = citations.validate_cells(
        [{"option": "A", "value": "V1", "score": True, "reason": "x", "cites": ["S1"], "depends_on_others": False}],
        ["A"], ["V1"], {"S1"},
    )
    assert cells[0]["insufficient"] is True


def test_scores_endpoint(monkeypatch):
    monkeypatch.setattr(ai, "call", lambda *a, **k: ({"cells": [], "crisis": False}, None))
    r = client.post("/api/scores", json={
        "options": [{"id": "A", "name": "Berlin"}, {"id": "B", "name": "San Francisco"}, {"id": "W", "name": "Wait / neither"}],
        "values": [{"id": "V1", "name": "Family nearby"}],
        "statements": [{"id": "S1", "title": "Family", "text": "I miss my family."}],
    })
    body = r.json()
    assert r.status_code == 200 and len(body["cells"]) == 3 and all(c["insufficient"] for c in body["cells"])
