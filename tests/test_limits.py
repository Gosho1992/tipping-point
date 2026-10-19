"""Slice 8: caps and atomic spend protection."""
import threading

import pytest
from fastapi.testclient import TestClient

from server import ai, config, limits, main

client = TestClient(main.app)
OPTS3 = [{"id": "A", "name": "Quit"}, {"id": "B", "name": "Stay"}, {"id": "W", "name": "Wait / neither"}]
BODY = {"options": OPTS3, "statements": [{"id": "S1", "title": "Manager", "text": "My manager shouts at me."}]}
GOOD = {"cards": [{"option": "A", "sentences": [{"text": "You left.", "cites": ["S1"]}]}], "crisis": False}
USAGE = ai.Usage("gpt-6-luna", 1000, 200)  # costs (1000*0.10 + 200*0.50) / 1e6 = 0.0002


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setattr(limits, "DB_PATH", str(tmp_path / "usage.db"))
    monkeypatch.setattr(config, "LIMIT_VISITOR_CALLS", 1000)
    monkeypatch.setattr(config, "LIMIT_NETWORK_CALLS", 1000)
    monkeypatch.setattr(config, "LIMIT_GLOBAL_CALLS", 1000)
    monkeypatch.setattr(config, "DAILY_SPEND_CAP_USD", 1.0)


def post(visitor="v1"):
    return client.post("/api/futures", json=BODY, headers={"X-Visitor-Id": visitor})


def test_visitor_cap(monkeypatch):
    monkeypatch.setattr(config, "LIMIT_VISITOR_CALLS", 2)
    monkeypatch.setattr(ai, "call", lambda *a, **k: (GOOD, USAGE))
    assert post().status_code == 200 and post().status_code == 200
    r = post()
    assert r.status_code == 429 and r.json() == {"code": "limit_visitor"}
    assert post("v2").status_code == 200  # another visitor is unaffected


def test_network_cap_catches_cleared_visitor_id(monkeypatch):
    monkeypatch.setattr(config, "LIMIT_NETWORK_CALLS", 2)
    monkeypatch.setattr(ai, "call", lambda *a, **k: (GOOD, USAGE))
    assert post("a").status_code == 200 and post("b").status_code == 200
    assert post("c").json() == {"code": "limit_network"}


def test_global_cap(monkeypatch):
    monkeypatch.setattr(config, "LIMIT_GLOBAL_CALLS", 1)
    monkeypatch.setattr(ai, "call", lambda *a, **k: (GOOD, USAGE))
    assert post("a").status_code == 200
    assert post("b").json() == {"code": "limit_global"}


def test_budget_cap_blocks_before_calling(monkeypatch):
    monkeypatch.setattr(config, "DAILY_SPEND_CAP_USD", 0.0001)  # below one call's worst case
    monkeypatch.setattr(ai, "call", lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not call")))
    assert post().json() == {"code": "limit_budget"}


def test_actual_cost_replaces_reservation():
    res = limits.reserve("visitor:x", "net:x", "gpt-6-luna", 3000, 1000)
    assert limits.snapshot()["global"]["reserved"] == pytest.approx(res.estimate)
    spent = limits.settle(res, USAGE, keep=True)
    snap = limits.snapshot()["global"]
    assert spent == pytest.approx(0.0002) and snap["cost"] == pytest.approx(0.0002) and snap["reserved"] == pytest.approx(0)


def test_cost_recorded_even_when_validation_fails(monkeypatch):
    bad = {"cards": [{"option": "A", "sentences": [{"text": "Invented.", "cites": ["S99"]}]}], "crisis": False}
    monkeypatch.setattr(ai, "call", lambda *a, **k: (bad, USAGE))
    r = post()
    assert r.status_code == 200 and r.json()["cards"][0]["sentences"] == []
    assert limits.snapshot()["global"]["cost"] == pytest.approx(0.0002)


def test_bad_json_reply_still_counts(monkeypatch):
    def fail(*a, **k):
        raise ai.AIError("bad_json", maybe_billed=True, usage=USAGE)
    monkeypatch.setattr(ai, "call", fail)
    assert post().status_code == 502
    assert limits.snapshot()["global"]["cost"] == pytest.approx(0.0002)


def test_timeout_keeps_full_reservation(monkeypatch):
    def fail(*a, **k):
        raise ai.AIError("timeout", maybe_billed=True)
    monkeypatch.setattr(ai, "call", fail)
    assert post().status_code == 502
    snap = limits.snapshot()["global"]
    assert snap["cost"] > 0.0002 and snap["reserved"] == pytest.approx(0) and snap["calls"] == 1


def test_refused_connection_releases_reservation_and_call(monkeypatch):
    def fail(*a, **k):
        raise ai.AIError("connection", maybe_billed=False)
    monkeypatch.setattr(ai, "call", fail)
    assert post().status_code == 502
    snap = limits.snapshot()
    assert snap["global"]["cost"] == 0 and snap["global"]["reserved"] == 0 and snap["global"]["calls"] == 0
    assert snap["visitor:v1"]["calls"] == 0


def test_concurrent_reservations_never_exceed_budget(monkeypatch):
    est = limits.estimate_usd("gpt-6-luna", 3000, 1000)
    monkeypatch.setattr(config, "DAILY_SPEND_CAP_USD", est * 5.5)  # room for exactly 5
    results = []

    def worker(i):
        try:
            limits.reserve(f"visitor:{i}", f"net:{i}", "gpt-6-luna", 3000, 1000)
            results.append("ok")
        except limits.LimitError as e:
            results.append(e.code)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert results.count("ok") == 5 and results.count("limit_budget") == 15
    assert limits.snapshot()["global"]["reserved"] <= config.DAILY_SPEND_CAP_USD


def test_daily_reset(monkeypatch):
    monkeypatch.setattr(config, "LIMIT_VISITOR_CALLS", 1)
    monkeypatch.setattr(ai, "call", lambda *a, **k: (GOOD, USAGE))
    monkeypatch.setattr(limits, "today", lambda: "2026-10-18")
    assert post().status_code == 200 and post().status_code == 429
    monkeypatch.setattr(limits, "today", lambda: "2026-10-19")
    assert post().status_code == 200


def test_ip_is_stored_only_as_a_hash():
    assert limits.network_key("203.0.113.9").startswith("net:") and "203.0.113.9" not in limits.network_key("203.0.113.9")
    assert limits.visitor_key("<script>") == "visitor:anonymous"
