"""Citation support test: run each scenario through the real endpoints (live AI) and write a review sheet.

Usage:  python -m tests.run_scenarios <scenario>     (ayesha | ambiguous | contradictory | thin | crisis | all)
Runs are resumable: progress is saved after every AI call in tests/scenarios/out/<scenario>.json,
so re-run the same command until it prints DONE. Then open tests/scenarios/out/review.md and mark each item.
"""
import json
import logging
import re
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from server import main

HERE = Path(__file__).parent / "scenarios"
OUT = HERE / "out"
OUT.mkdir(exist_ok=True)
FIRST_Q = "Why does this decision matter to you right now?"
client = TestClient(main.app)


class Counter(logging.Handler):
    def __init__(self):
        super().__init__()
        self.counts = {}

    def emit(self, record):
        for k, v in re.findall(r"(\w+)=(\d+)", record.getMessage()):
            if k in ("quote_mismatch", "themes_removed", "cells_converted_or_missing", "removed", "converted_or_missing"):
                key = f"{record.getMessage().split(':')[0]}.{k}"
                self.counts[key] = self.counts.get(key, 0) + int(v)


def run(name: str) -> bool:
    sc = json.loads((HERE / f"{name}.json").read_text(encoding="utf-8"))
    path = OUT / f"{name}.json"
    st = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {
        "turn": 0, "statements": [], "themes": [], "asked": [], "question": FIRST_Q, "next": 1,
        "crisis_at": None, "cells": None, "futures": None, "counts": {}}
    options = [{"id": "A", "name": sc["options"][0]}, {"id": "B", "name": sc["options"][1]}, {"id": "W", "name": "Wait / neither"}]
    counter = Counter()
    logging.getLogger("tippingpoint").addHandler(counter)

    def stmts():
        return [{"id": s["id"], "title": s["title"], "text": s["text"]} for s in st["statements"]]

    def persist():
        for k, v in counter.counts.items():
            st["counts"][k] = st["counts"].get(k, 0) + v
        counter.counts.clear()
        path.write_text(json.dumps(st, indent=1, ensure_ascii=False), encoding="utf-8")

    while st["crisis_at"] is None and st["turn"] < len(sc["answers"]):
        ans = sc["answers"][st["turn"]]
        r = client.post("/api/turn", json={"decision": sc["decision"], "options": options, "asked": st["asked"],
                                           "question": st["question"], "answer": ans, "statements": stmts(), "next_number": st["next"]})
        body = r.json()
        st["turn"] += 1
        if body.get("crisis"):
            st["crisis_at"] = st["turn"]; persist(); break
        if r.status_code != 200:
            print("turn failed:", body); persist(); return False
        for s in body["statements"]:
            s["answer"] = ans
            st["statements"].append(s)
            st["next"] = max(st["next"], int(s["id"][1:]) + 1)
        st["themes"] = body["themes"]
        st["asked"].append(st["question"]); st["question"] = body["next_question"]
        persist()
        print(f"{name}: answer {st['turn']} done")

    if st["crisis_at"] is None and st["cells"] is None:
        values = [{"id": t["id"], "name": t["name"]} for t in st["themes"]] or [{"id": "T1", "name": "What matters"}]
        r = client.post("/api/scores", json={"options": options, "values": values, "statements": stmts()})
        if r.status_code != 200:
            print("scores failed:", r.json()); persist(); return False
        st["cells"] = r.json()["cells"]; persist(); print(f"{name}: scores done")
    if st["crisis_at"] is None and st["futures"] is None:
        r = client.post("/api/futures", json={"options": options, "statements": stmts()})
        if r.status_code != 200:
            print("futures failed:", r.json()); persist(); return False
        st["futures"] = r.json()["cards"]; persist(); print(f"{name}: futures done")
    return True


def sheet() -> str:
    lines = ["# Citation support review", "",
             "Mark every item: **S** supported, **P** partly, **N** not supported — judged only against the cited statements.",
             "Pass bar for the Ayesha demo: at least 90% S, and no N item that would appear on the board.", ""]
    for f in sorted(OUT.glob("*.json")):
        st = json.loads(f.read_text(encoding="utf-8"))
        sc = json.loads((HERE / f.name).read_text(encoding="utf-8"))
        opt = {"A": sc["options"][0], "B": sc["options"][1], "W": "Wait / neither"}
        sid = {s["id"]: s for s in st["statements"]}
        quote = lambda ids: "; ".join(f'{i} "{sid[i]["text"]}"' for i in ids if i in sid)
        lines += [f"## {sc['name']} ({f.stem})", ""]
        if st["crisis_at"]:
            lines += [f"Flow stopped with the support message at answer {st['crisis_at']} (expected: {sc['expect']}).", ""]
            continue
        lines += ["**Statements**", ""]
        for s in st["statements"]:
            lines.append(f"- {s['id']} {s['title']}: {s['text']} — quote {'verified' if s['quoteVerified'] else 'NOT verified'}")
        lines += ["", "**Themes**", ""]
        for t in st["themes"]:
            lines.append(f"- [ ] {t['name']} ← {quote(t['cites'])}")
        lines += ["", "**Score reasons**", ""]
        names = {t["id"]: t["name"] for t in st["themes"]}
        for c in st["cells"] or []:
            if c["insufficient"]:
                lines.append(f"- (not enough) {opt[c['option']]} × {names.get(c['value'], c['value'])}")
            else:
                dep = " · depends on others" if c["depends_on_others"] else ""
                lines.append(f"- [ ] {opt[c['option']]} × {names.get(c['value'], c['value'])} = {c['score']}{dep}: \"{c['reason']}\" ← {quote(c['cites'])}")
        lines += ["", "**Future sentences**", ""]
        for card in st["futures"] or []:
            for s in card["sentences"]:
                lines.append(f"- [ ] {opt[card['option']]}: \"{s['text']}\" ← {quote(s['cites'])}")
            if not card["sentences"]:
                lines.append(f"- (not enough) {opt[card['option']]}")
        lines += ["", f"Validator counts: {st['counts'] or 'none removed'}", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    names = [p.stem for p in sorted(HERE.glob("*.json"))] if sys.argv[1:] == ["all"] else sys.argv[1:]
    ok = all(run(n) for n in names)
    (OUT / "review.md").write_text(sheet(), encoding="utf-8")
    print("DONE" if ok else "INCOMPLETE — run again to resume")
