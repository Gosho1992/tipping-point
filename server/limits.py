"""Usage caps and spend protection. Stores counts and costs only — never anyone's text.

Every AI call: reserve (atomic check + book the worst-case cost) -> call -> settle (replace the booking with
the real cost as soon as the response arrives, or keep/release it on failure).
This cap is best-effort: it only sees this app's calls and its prices are copies. The OpenAI project budget is the hard backstop.
"""
import hashlib
import os
import re
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone

from . import config

DB_PATH = os.getenv("USAGE_DB", str(config.ROOT / "server" / "usage.db"))
_init_lock = threading.Lock()
_initialized = set()
_VISITOR_RX = re.compile(r"^[A-Za-z0-9-]{1,64}$")


class LimitError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass
class Reservation:
    day: str
    keys: list
    estimate: float
    model: str


def today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=15, isolation_level=None)
    with _init_lock:
        if DB_PATH not in _initialized:
            conn.execute("CREATE TABLE IF NOT EXISTS usage (day TEXT, key TEXT, calls INTEGER DEFAULT 0, "
                         "cost_usd REAL DEFAULT 0, reserved_usd REAL DEFAULT 0, PRIMARY KEY (day, key))")
            _initialized.add(DB_PATH)
    return conn


def visitor_key(header_value: str | None) -> str:
    v = (header_value or "").strip()
    return f"visitor:{v if _VISITOR_RX.match(v) else 'anonymous'}"


def network_key(ip: str | None) -> str:
    digest = hashlib.sha256(f"{config.IP_HASH_SALT}|{ip or 'unknown'}".encode()).hexdigest()[:20]
    return f"net:{digest}"


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    p_in, p_out = config.price_per_m(model)
    return (input_tokens * p_in + output_tokens * p_out) / 1_000_000


def estimate_usd(model: str, prompt_chars: int, max_output_tokens: int) -> float:
    # ~3 characters per token errs high for English; output assumes the full cap is used.
    return cost_usd(model, prompt_chars // 3 + 50, max_output_tokens)


def reserve(visitor: str, network: str, model: str, prompt_chars: int, max_output_tokens: int) -> Reservation:
    day = today()
    est = estimate_usd(model, prompt_chars, max_output_tokens)
    caps = {visitor: (config.LIMIT_VISITOR_CALLS, "limit_visitor"),
            network: (config.LIMIT_NETWORK_CALLS, "limit_network"),
            "global": (config.LIMIT_GLOBAL_CALLS, "limit_global")}
    conn = _conn()
    try:
        conn.execute("BEGIN IMMEDIATE")
        rows = {k: conn.execute("SELECT calls, cost_usd, reserved_usd FROM usage WHERE day=? AND key=?", (day, k)).fetchone()
                or (0, 0.0, 0.0) for k in caps}
        for k, (cap, code) in caps.items():
            if rows[k][0] + 1 > cap:
                conn.execute("ROLLBACK")
                raise LimitError(code)
        g_calls, g_cost, g_reserved = rows["global"]
        if g_cost + g_reserved + est > config.DAILY_SPEND_CAP_USD:
            conn.execute("ROLLBACK")
            raise LimitError("limit_budget")
        for k in caps:
            conn.execute("INSERT INTO usage(day, key, calls) VALUES(?, ?, 1) ON CONFLICT(day, key) DO UPDATE SET calls = calls + 1", (day, k))
        conn.execute("UPDATE usage SET reserved_usd = reserved_usd + ? WHERE day=? AND key='global'", (est, day))
        conn.execute("COMMIT")
    finally:
        conn.close()
    return Reservation(day, list(caps), est, model)


def settle(res: Reservation, usage=None, keep: bool = True) -> float:
    """Replace the booking with the real cost. No usage: keep the full estimate if the call may have been billed,
    otherwise release it and give the call back. Returns the cost recorded."""
    if usage is not None:
        spent = cost_usd(usage.model, usage.input_tokens, usage.output_tokens)
    elif keep:
        spent = res.estimate
    else:
        spent = 0.0
    conn = _conn()
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("UPDATE usage SET reserved_usd = MAX(0, reserved_usd - ?), cost_usd = cost_usd + ? WHERE day=? AND key='global'",
                     (res.estimate, spent, res.day))
        if usage is None and not keep:
            for k in res.keys:
                conn.execute("UPDATE usage SET calls = MAX(0, calls - 1) WHERE day=? AND key=?", (res.day, k))
        conn.execute("COMMIT")
    finally:
        conn.close()
    return spent


def snapshot(day: str | None = None) -> dict:
    conn = _conn()
    try:
        rows = conn.execute("SELECT key, calls, cost_usd, reserved_usd FROM usage WHERE day=?", (day or today(),)).fetchall()
    finally:
        conn.close()
    return {k: {"calls": c, "cost": cost, "reserved": r} for k, c, cost, r in rows}
