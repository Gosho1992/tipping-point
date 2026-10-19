"""Citation and source checks. A valid ID or quote proves the source exists, not that it supports the claim."""
import re

_WS = re.compile(r"\s+")


def _norm(s: str) -> str:
    s = (s or "").replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return _WS.sub(" ", s).strip().lower()


def quote_in_answer(quote: str, answer: str) -> bool:
    q = _norm(quote).strip(" .,;:!?\"'")
    return len(q) >= 3 and q in _norm(answer)


def clean_statements(items: list, answer: str) -> tuple[list, int]:
    """Trim, drop empty statements, and mark whether each quote really appears in the answer."""
    out, mismatched = [], 0
    for it in items or []:
        title = (it.get("title") or "").strip()[:80]
        text = (it.get("text") or "").strip()[:300]
        quote = (it.get("quote") or "").strip()[:600]
        if not text:
            continue
        ok = quote_in_answer(quote, answer)
        if not ok:
            mismatched += 1
        out.append({"title": title or text[:40], "text": text, "quote": quote if ok else "", "quoteVerified": ok})
    return out, mismatched


def validate_values(values: list, valid_ids: set) -> tuple[list, int]:
    """Keep only values whose citations are non-empty and all point to current statements."""
    out, removed, seen = [], 0, set()
    for v in values or []:
        name = (v.get("name") or "").strip()[:60]
        cites = [c.strip() for c in (v.get("cites") or []) if isinstance(c, str)]
        if not name or not cites or any(c not in valid_ids for c in cites) or name.lower() in seen:
            removed += 1
            continue
        seen.add(name.lower())
        out.append({"name": name, "cites": sorted(set(cites), key=cites.index)})
    return out[:6], removed + max(0, len(out) - 6)


def _insufficient(o: str, v: str) -> dict:
    return {"option": o, "value": v, "score": None, "reason": "", "cites": [], "depends_on_others": False, "insufficient": True}


def validate_cells(cells: list, option_ids: list, value_ids: list, valid_ids: set) -> tuple[list, int]:
    """Always return the complete option x value grid. Unsupported cells become explicit insufficient cells."""
    grid = {(o, v): None for o in option_ids for v in value_ids}
    converted = 0
    for c in cells or []:
        key = (c.get("option"), c.get("value"))
        if key not in grid or grid[key] is not None:
            continue  # unknown option/value, or a duplicate
        score = c.get("score")
        cites = [x for x in (c.get("cites") or []) if isinstance(x, str)]
        ok_score = isinstance(score, int) and not isinstance(score, bool) and 0 <= score <= 10
        if score is None:
            grid[key] = _insufficient(*key)
        elif not ok_score or not cites or any(x not in valid_ids for x in cites):
            grid[key] = _insufficient(*key)
            converted += 1
        else:
            grid[key] = {
                "option": key[0], "value": key[1], "score": score,
                "reason": (c.get("reason") or "").strip()[:200],
                "cites": sorted(set(cites), key=cites.index),
                "depends_on_others": bool(c.get("depends_on_others")),
                "insufficient": False,
            }
    missing = sum(1 for k, val in grid.items() if val is None)
    out = [grid[k] or _insufficient(*k) for k in grid]
    return out, converted + missing


_NID = re.compile(r"^N(\d+)$")


def renumber_new(statements: list, answer: str, next_number: int) -> tuple[list, dict, int]:
    """Clean new statements and give them real IDs (S<next>...). Returns (statements, N->S map, quote mismatches)."""
    cleaned, mismatched = [], 0
    mapping: dict = {}
    n = next_number
    for it in statements or []:
        kept, mm = clean_statements([it], answer)
        mismatched += mm
        if not kept:
            continue
        local = (it.get("id") or "").strip()
        sid = f"S{n}"
        n += 1
        if _NID.match(local) and local not in mapping:
            mapping[local] = sid
        cleaned.append({"id": sid, **kept[0]})
    return cleaned, mapping, mismatched


def map_cites(cites: list, mapping: dict) -> list:
    return [mapping.get(c, c) for c in (cites or []) if isinstance(c, str)]


def validate_themes(themes: list, valid_ids: set, mapping: dict) -> tuple[list, int]:
    """Themes must cite at least one current statement and nothing unknown. Keeps the AI's theme IDs when unique."""
    out, removed, seen_ids, seen_names = [], 0, set(), set()
    for t in themes or []:
        tid = (t.get("id") or "").strip()[:8]
        name = (t.get("name") or "").strip()[:60]
        cites = map_cites(t.get("cites"), mapping)
        if (not tid or tid in seen_ids or not name or name.lower() in seen_names
                or not cites or any(c not in valid_ids for c in cites)):
            removed += 1
            continue
        seen_ids.add(tid); seen_names.add(name.lower())
        out.append({"id": tid, "name": name, "cites": sorted(set(cites), key=cites.index)})
    return out[:6], removed + max(0, len(out) - 6)


def validate_futures(cards: list, option_ids: list, valid_ids: set) -> tuple[list, int]:
    """One card per option; only sentences with valid citations survive. An empty card is allowed (shown as 'not enough')."""
    by = {o: None for o in option_ids}
    removed = 0
    for card in cards or []:
        o = card.get("option")
        if o not in by or by[o] is not None:
            continue
        kept = []
        for snt in card.get("sentences") or []:
            text = (snt.get("text") or "").strip()[:220]
            cites = [c for c in (snt.get("cites") or []) if isinstance(c, str)]
            if not text or not cites or any(c not in valid_ids for c in cites):
                removed += 1
                continue
            kept.append({"text": text, "cites": sorted(set(cites), key=cites.index)})
        by[o] = kept[:4]
        removed += max(0, len(kept) - 4)
    return [{"option": o, "sentences": by[o] or []} for o in option_ids], removed
